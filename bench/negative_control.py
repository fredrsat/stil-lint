"""Negativ kontroll (del 8, punkt 2): kjør linteren på menneskeskrevet
før-2022-tekst og mål falsk-positiv-rate per regel.

Dokumentets regel: en regel som flagger over 5 % av rene avsnitt, blir
rådgivende til den er omskrevet. Skriver også et utvalg avsnitt som ikke ble
flagget til bench/data/clean_paragraphs.jsonl - grunnlaget for
seeded-fault-evalueringen i steg 8.

Kjør: .venv/bin/python bench/negative_control.py [antall, default 500]
"""

from __future__ import annotations

import asyncio
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from stillint.engine import Engine  # noqa: E402

BENCH = Path(__file__).resolve().parent
NOREC = BENCH / "data" / "norec" / "data"
OUT = BENCH / "data" / "clean_paragraphs.jsonl"
FP_LIMIT = 0.05
MIN_WORDS, MAX_WORDS = 40, 150


def sample_paragraphs(n: int, seed: int = 42) -> list[dict]:
    meta = json.load(open(NOREC / "metadata.json"))
    nb = [k for k, v in meta.items() if v.get("language") == "nb" and (v.get("year") or 0) <= 2019]
    rng = random.Random(seed)
    rng.shuffle(nb)
    out: list[dict] = []
    for doc_id in nb:
        split = meta[doc_id]["split"]
        path = NOREC / split / f"{int(doc_id):06d}.txt"
        if not path.exists():
            continue
        # NoReC har én setning per linje; blanklinje skiller avsnitt.
        for block in re.split(r"\n\s*\n", path.read_text(errors="ignore"))[1:]:  # hopp over tittel
            text = " ".join(ln.strip() for ln in block.splitlines() if ln.strip())
            words = len(text.split())
            if MIN_WORDS <= words <= MAX_WORDS:
                out.append({"doc": doc_id, "category": meta[doc_id].get("category"),
                            "year": meta[doc_id].get("year"), "text": text})
                break  # maks ett avsnitt per dokument
        if len(out) >= n:
            break
    return out


async def main(n: int, mode: str = "fast") -> None:
    paragraphs = sample_paragraphs(n)
    engine = Engine()
    flagged: Counter = Counter()
    clean: list[dict] = []

    for para in paragraphs:
        result = await engine.check_text(para["text"], genre="sakprosa", mode=mode)
        rules = {f["rule"] for f in result["findings"]}
        for rule in rules:
            flagged[rule] += 1
        if not rules:
            clean.append(para)

    total = len(paragraphs)
    print(f"# Negativ kontroll: {total} avsnitt fra NoReC (bokmål, t.o.m. 2019), mode={mode}\n")
    print("| regel | flagget | andel | status |")
    print("| --- | --- | --- | --- |")
    for rule, count in flagged.most_common():
        rate = count / total
        status = f"**OVER {FP_LIMIT:.0%} - settes rådgivende**" if rate > FP_LIMIT else "ok"
        print(f"| {rule} | {count} | {rate:.1%} | {status} |")
    if not flagged:
        print("| (ingen) | 0 | 0% | ok |")

    # Bare fast-modus definerer seed-settet; full-modus skal ikke krympe det.
    if mode == "fast":
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUT, "w") as fh:
            for para in clean:
                fh.write(json.dumps(para, ensure_ascii=False) + "\n")
        print(f"\n{len(clean)} uflaggede avsnitt skrevet til {OUT.relative_to(BENCH.parent)}")


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 500,
                     sys.argv[2] if len(sys.argv) > 2 else "fast"))
