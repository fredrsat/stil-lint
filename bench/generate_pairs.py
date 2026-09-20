"""Steg 5: parvise norske data etter Reinhart-metoden.

Tar rene NoReC-avsnitt (fra negative_control.py), gir en LLM åpningen og ber
den fortsette. Da er tema, sjanger og lengde kontrollert, og forskjellen
mellom menneskets fortsettelse og modellens er selve signalet.

To varianter per modell: nøytral, og "uformelt og menneskelig" (gruppen der
verktøy vanligvis svikter). Resultatet skrives løpende til
bench/data/llm_pairs.jsonl; skriptet kan kjøres på nytt og hopper over
ferdige kombinasjoner.

Kjør: OPENROUTER_API_KEY=... .venv/bin/python bench/generate_pairs.py [antall, default 100]
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

import httpx

BENCH = Path(__file__).resolve().parent
CLEAN = BENCH / "data" / "clean_paragraphs.jsonl"
OUT = BENCH / "data" / "llm_pairs.jsonl"

MODELS = [
    "openai/gpt-5.4-mini",
    "anthropic/claude-sonnet-4.6",
    "meta-llama/llama-4-maverick",
    "google/gemini-3.8-flash",
]
VARIANTS = {
    "noytral": "",
    "menneskelig": " Skriv uformelt og menneskelig, slik en vanlig person ville skrevet.",
}
CONCURRENCY = 8
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÆØÅ«\"])")


def split_opening(text: str) -> tuple[str, str] | None:
    sents = SENT_SPLIT.split(text.strip())
    opening, rest = "", sents
    while rest and len(opening.split()) < 12:
        opening = (opening + " " + rest[0]).strip()
        rest = rest[1:]
    human_rest = " ".join(rest).strip()
    if len(opening.split()) < 12 or len(human_rest.split()) < 30:
        return None
    return opening, human_rest


def prompt_for(opening: str, target_words: int, variant: str) -> str:
    return (
        "Dette er begynnelsen på et avsnitt fra en norsk anmeldelse. "
        f"Fortsett avsnittet på norsk med omtrent {target_words} ord."
        f"{VARIANTS[variant]} "
        "Svar bare med selve fortsettelsen, uten innledning, kommentarer eller formatering.\n\n"
        f"{opening}"
    )


async def generate(client: httpx.AsyncClient, sem: asyncio.Semaphore, key: str,
                   model: str, prompt: str) -> str | None:
    async with sem:
        for attempt in range(4):
            try:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}"},
                    json={"model": model, "max_tokens": 2000,
                          "messages": [{"role": "user", "content": prompt}]},
                    timeout=90.0,
                )
                if resp.status_code == 200:
                    content = (resp.json().get("choices") or [{}])[0].get("message", {}).get("content")
                    if content and content.strip():
                        return content.strip()
                    # tomt svar (f.eks. resonneringstoken brukte opp budsjettet): prøv igjen
                elif resp.status_code not in (429, 500, 502, 503):
                    print(f"  {model}: HTTP {resp.status_code} {resp.text[:120]}", file=sys.stderr)
                    return None
            except httpx.HTTPError as exc:
                print(f"  {model}: {exc!r}", file=sys.stderr)
            await asyncio.sleep(2 ** attempt)
    return None


async def main(n: int) -> None:
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("TYPESAFE_API_KEY")
    if not key:
        sys.exit("Sett OPENROUTER_API_KEY.")

    pairs = []
    for line in CLEAN.read_text().splitlines():
        para = json.loads(line)
        split = split_opening(para["text"])
        if split:
            pairs.append({**para, "opening": split[0], "human_rest": split[1]})
        if len(pairs) >= n:
            break

    done = set()
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            row = json.loads(line)
            done.add((row["doc"], row["model"], row["variant"]))

    sem = asyncio.Semaphore(CONCURRENCY)
    todo = [(p, m, v) for p in pairs for m in MODELS for v in VARIANTS
            if (p["doc"], m, v) not in done]
    print(f"{len(pairs)} åpninger, {len(todo)} genereringer igjen "
          f"({len(done)} alt gjort)", file=sys.stderr)

    async with httpx.AsyncClient() as client:
        with open(OUT, "a") as fh:
            async def run_one(p, model, variant):
                target = len(p["human_rest"].split())
                text = await generate(client, sem, key, model,
                                      prompt_for(p["opening"], target, variant))
                if text:
                    fh.write(json.dumps({
                        "doc": p["doc"], "category": p["category"], "year": p["year"],
                        "opening": p["opening"], "human_rest": p["human_rest"],
                        "model": model, "variant": variant, "llm_text": text,
                    }, ensure_ascii=False) + "\n")
                    fh.flush()
                return text is not None

            results = await asyncio.gather(*(run_one(p, m, v) for p, m, v in todo))
    ok = sum(results)
    print(f"Ferdig: {ok} av {len(todo)} genereringer lyktes. Skrev {OUT}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 100))
