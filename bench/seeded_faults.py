"""Steg 8: seeded-fault-evaluering (metoden fra snifftest).

Tar rene NoReC-avsnitt (negative_control.py), planter én kjent feil per regel
i kopier, og måler fanget andel per regel. Regex-/statregler kjøres i
mode=fast (validerer rørleggingen); Jev-reglene i mode=full. For Jev-reglene
kjøres i tillegg samme feil med engelsk spørsmålstekst, for å avgjøre det
åpne spørsmålet fra researchdokumentet del 3: virker norske spørsmål om norsk
tekst bedre enn engelske?

Kjør: TYPESAFE_API_KEY=... .venv/bin/python bench/seeded_faults.py [n_per_regel, default 10]
"""

from __future__ import annotations

import asyncio
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from stillint.engine import Engine  # noqa: E402

BENCH = Path(__file__).resolve().parent
CLEAN = BENCH / "data" / "clean_paragraphs.jsonl"

# Injektorer: tar et rent avsnitt, returnerer kopi med én plantet feil.
# Hver injektor er godkjent manuelt mot regelens `what`/`not_for`.
LEX_FAULTS = {
    "A02_stilord_nb": lambda t: t + " Dette er en sømløs og banebrytende løsning som gir verdifull innsikt.",
    "A03_skiltfraser": lambda t: "Det er viktig å merke seg at " + t[0].lower() + t[1:],
    "A04_chatbotrester": lambda t: t + " Håper dette hjelper!",
    "A05_forsterkere": lambda t: t + " Det er ærlig talt helt ærlig rett og slett virkelig faktisk utrolig bra.",
    "A09_smisk": lambda t: "Det er helt forståelig at du lurer. " + t,
    "A12_llm_ngram_validert": lambda t: t + " Det høres kanskje rart ut, men resultatet er en opplevelse som føles både rå og ekte.",
    "B01_tankestrek": lambda t: t.replace(", ", "—", 2) if t.count(", ") >= 2 else t + " Dette—altså—gjelder.",
    "B02_kolonavsloring": lambda t: "Poenget: " + t,
    "C09_dramatiske_fragmenter": lambda t: t + " Enkelt. Effektivt. Trygt.",
    "C10_noe_som_hale": lambda t: t + " Dette gjelder mange, noe som understreker betydningen av god informasjon.",
    "D03_vag_kilde": lambda t: t + " Studier viser at dette stemmer for de fleste.",
    "D10_menyavslutning": lambda t: t + " Vil du at jeg skal utdype noen av punktene?",
    "E03_stedsformat": lambda t: t + " Dette skjedde i Lillehammer, Norge.",
    "E06_preposisjonskalker": lambda t: t + " Mange bruker dette på daglig basis.",
}

JEV_FAULTS = {
    "C01_negativ_parallellisme": lambda t: t + " Dette er ikke bare underholdning, det er en helt ny måte å oppleve historien på.",
    "C02_tvunget_tretall": lambda t: t + " Alt oppleves raskt, enkelt og effektivt.",
    "C04_oppsummerende_slutt": lambda t: t + " Til syvende og sist handler alt om kvalitet.",
    "C06_halsrensk": lambda t: "I dagens samfunn er det mange som lurer på nettopp dette. La oss se nærmere på saken.\n\n" + t,
    "C10_pahengt_tolkning": lambda t: t + " Dette er gjennomført, noe som understreker hvor viktig helheten er.",
    "D02_betydningsoppblasing": lambda t: t + " Dette markerer et vendepunkt og er et viktig skritt i en større utvikling.",
    "D05_folelse_ikke_mekanisme": lambda t: t + " Løsningen føles trygg, sømløs og gjennomarbeidet.",
    "E01_oversatt_engelsk": lambda t: t + " På slutten av dagen gjør det en forskjell at man tok et øyeblikk.",
}

# Engelsk oversettelse av de samme Jev-spørsmålene (nb-mot-en-testen).
EN_QUESTIONS = {
    "C01_negativ_parallellisme": (
        "At least one sentence rejects a label only to replace it with another "
        "(\"not just X, but Y\", \"it's not about X, it's about Y\"), where the rejection "
        "does not answer anything the reader actually believed.",
        {"true": "At least one sentence has a contrast turn that is decoration, not correction.",
         "false": "No contrast turn, or the contrast corrects a real misunderstanding."}),
    "C02_tvunget_tretall": (
        "A list has three coordinated items (\"fast, safe and simple\") where the items are "
        "not three clearly different things: at least one item repeats, overlaps with or adds "
        "nothing beyond the others.",
        {"true": "At least one three-item list where the items are not three genuinely different things.",
         "false": "No three-item list, or every item is individually necessary."}),
    "C04_oppsummerende_slutt": (
        "The paragraph's last sentence adds no new information: it repeats what the paragraph "
        "already said, or lands on a generic wisdom.",
        {"true": "The last sentence is pure repetition or pasted-on wisdom.",
         "false": "The last sentence adds something the reader has not already been given."}),
    "C06_halsrensk": (
        "The opening delays the content: it repeats the question, sets the scene (\"In today's "
        "digital world\") or promises what the text will cover, instead of starting with the substance.",
        {"true": "The first paragraph could be deleted without the reader losing anything.",
         "false": "The first paragraph contains information or a position the reader needs."}),
    "C10_pahengt_tolkning": (
        "A sentence consists of a fact plus an appended interpretation of that fact in the same "
        "sentence (\"..., which underscores the importance of ...\"), where the interpretation is "
        "generic and does not follow from the fact alone.",
        {"true": "At least one sentence has an appended, generic interpretive tail.",
         "false": "No interpretive tails, or the tails carry concrete content."}),
    "D02_betydningsoppblasing": (
        "A routine fact is inflated into something big: a turning point, a milestone, part of a "
        "larger development or \"an important step\", without the text substantiating why it is big.",
        {"true": "At least one routine fact is inflated without substantiation.",
         "false": "Facts are described at their actual size."}),
    "D05_folelse_ikke_mekanisme": (
        "The text says how something feels (safe, simple, powerful, seamless) without saying what "
        "it does or how it works.",
        {"true": "The paragraph has experience words without a single mechanism behind them.",
         "false": "The paragraph explains what the thing does."}),
    "E01_oversatt_engelsk": (
        "The Norwegian text reads like translated English: idioms, word order or preposition use "
        "that is unusual in Norwegian but common in English.",
        {"true": "At least one phrasing a Norwegian writer would not choose, but a direct translation explains.",
         "false": "The text reads as idiomatic Norwegian."}),
}


def load_paragraphs(n_total: int, seed: int = 7) -> list[str]:
    rows = [json.loads(ln)["text"] for ln in CLEAN.read_text().splitlines()]
    rng = random.Random(seed)
    rng.shuffle(rows)
    return rows[:n_total]


async def eval_arm(engine: Engine, faults: dict, paragraphs: list[str], mode: str,
                   label: str) -> None:
    print(f"## {label}\n")
    print("| regel | plantede | fanget | andel | ingen-vurdering | andre funn/tekst |")
    print("| --- | --- | --- | --- | --- | --- |")
    for rule_id, inject in faults.items():
        caught = nj = other = 0
        for text in paragraphs:
            faulted = inject(text)
            res = await engine.check_text(faulted, genre="sakprosa", mode=mode)
            hits = {f["rule"] for f in res["findings"]}
            caught += rule_id in hits
            nj += rule_id in res["no_judgment"]
            other += len(hits - {rule_id})
        n = len(paragraphs)
        print(f"| {rule_id} | {n} | {caught} | {caught/n:.0%} | {nj} | {other/n:.1f} |")
    print()


async def main(n_per_rule: int) -> None:
    paragraphs = load_paragraphs(n_per_rule)
    engine = Engine()

    print(f"# Seeded-fault-evaluering: {n_per_rule} rene avsnitt per regel\n")
    print("Feilene er plantet med faste maler (én per regel). Avsnittene er")
    print("uflaggede NoReC-avsnitt fra negativ kontroll.\n")

    await eval_arm(engine, LEX_FAULTS, paragraphs, "fast", "Regex-/statregler, mode=fast")
    await eval_arm(engine, JEV_FAULTS, paragraphs, "full", "Jev-regler, norsk spørsmålstekst (mode=full)")

    # Engelsk spørsmålstekst: bytt what/criteria og kjør samme feil på nytt.
    for rule_id, (what_en, crit_en) in EN_QUESTIONS.items():
        rule = engine.config.by_id(rule_id)
        if rule:
            rule.what, rule.criteria = what_en, crit_en
    await eval_arm(engine, JEV_FAULTS, paragraphs, "full", "Jev-regler, engelsk spørsmålstekst (mode=full)")

    print("Merk: n er lite; les andeler mot variasjon mellom kjøringer, jf.")
    print("researchdokumentets forbehold. Cache gjør at re-kjøring med samme")
    print("tekster og spørsmål gir identiske tall.")


if __name__ == "__main__":
    asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 10))
