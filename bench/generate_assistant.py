"""Steg 5b: assistent-registeret. Fortsettelses-oppsettet (generate_pairs.py)
fikk modellene til å herme anmeldersjangeren og undertrykte assistent-stilen.
Her får de samme fire modellene oppgaver i registeret agentene faktisk skriver i:
svar på spørsmål, korte e-poster, varsler, råd og forklaringer.

Resultat: bench/data/llm_assistant.jsonl. Analyseres av assistant_ratio.py.

Kjør: OPENROUTER_API_KEY=... .venv/bin/python bench/generate_assistant.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx

from generate_pairs import MODELS, generate

BENCH = Path(__file__).resolve().parent
OUT = BENCH / "data" / "llm_assistant.jsonl"
CONCURRENCY = 8

# Oppgaver i fire sjangre. Ingen stilføringer: vi måler modellenes standardstil.
SPORSMAL = [
    "Hva er forskjellen på fastrente og flytende rente på boliglån?",
    "Hvorfor blir det nordlys?",
    "Hvordan fungerer varmepumpe når det er kaldt ute?",
    "Hva bør jeg tenke på når jeg velger barnesykkel?",
    "Hvorfor hever ikke gjærbaksten min?",
    "Hva er egentlig forskjellen på bokmål og nynorsk?",
    "Hvordan kommer jeg i gang med kompostering i hagen?",
    "Er det verdt å bytte til LED-pærer i hele huset?",
    "Hvordan lærer jeg barna mine å stå på ski?",
    "Hva gjør jeg hvis sykkelen min har fått åttetall i hjulet?",
    "Hvorfor bruker vi sommertid og vintertid?",
    "Hvordan velger jeg riktig turski til fjellet?",
]
EPOST = [
    "Skriv en kort e-post til naboen om at vi må felle et tre som henger over gjerdet deres.",
    "Skriv en e-post til skolen om at datteren min er syk og ikke kommer i dag.",
    "Skriv en e-post til utleier om at oppvaskmaskinen lekker.",
    "Skriv en e-post til treneren om at sønnen min slutter på fotballaget.",
    "Skriv en e-post til borettslaget med forslag om sykkelparkering i kjelleren.",
    "Skriv en e-post til kundeservice om en regning jeg mener er feil.",
    "Skriv en e-post der jeg takker nei til et jobbtilbud på en hyggelig måte.",
    "Skriv en e-post til legekontoret for å be om fornyelse av en resept.",
]
VARSEL = [
    "Skriv et kort push-varsel om at bussen til skolen er ti minutter forsinket.",
    "Skriv et kort varsel om at det blir regn fra klokka 14 og at paraply anbefales.",
    "Skriv et kort varsel om at strømprisen er høy mellom 17 og 20 i dag.",
    "Skriv et kort varsel om at matleveransen er flyttet til i morgen formiddag.",
    "Skriv et kort varsel om at leksene til matteprøven bør gjøres i kveld.",
    "Skriv et kort varsel om at det er glatte veier på skoleveien i morgen tidlig.",
]
RAD = [
    "Gi meg råd om hvordan jeg får tenåringen min til å legge seg tidligere.",
    "Gi meg råd om hva jeg bør gjøre med en kollega som alltid avbryter meg.",
    "Gi meg råd om hvordan jeg kommer i gang med løping etter mange år på sofaen.",
    "Gi meg råd om hvordan vi kan bruke mindre penger på dagligvarer.",
    "Gi meg råd om hvordan jeg holder motivasjonen oppe i mørketiden.",
    "Gi meg råd om hva jeg bør sjekke før jeg kjøper bruktbil.",
]
PROMPTS = ([("sporsmal", p) for p in SPORSMAL] + [("epost", p) for p in EPOST]
           + [("varsel", p) for p in VARSEL] + [("rad", p) for p in RAD])


async def main() -> None:
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("TYPESAFE_API_KEY")
    if not key:
        sys.exit("Sett OPENROUTER_API_KEY.")

    done = set()
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            row = json.loads(line)
            done.add((row["prompt"], row["model"]))

    todo = [(genre, prompt, model) for genre, prompt in PROMPTS for model in MODELS
            if (prompt, model) not in done]
    print(f"{len(PROMPTS)} oppgaver x {len(MODELS)} modeller, {len(todo)} igjen", file=sys.stderr)

    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient() as client:
        with open(OUT, "a") as fh:
            async def run_one(genre, prompt, model):
                text = await generate(client, sem, key, model, "Svar på norsk.\n\n" + prompt)
                if text:
                    fh.write(json.dumps({"genre": genre, "prompt": prompt, "model": model,
                                         "text": text}, ensure_ascii=False) + "\n")
                    fh.flush()
                return text is not None

            results = await asyncio.gather(*(run_one(g, p, m) for g, p, m in todo))
    print(f"Ferdig: {sum(results)} av {len(todo)} lyktes. Skrev {OUT}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
