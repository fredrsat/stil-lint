"""Steg 5b, analyse: presenslistene mot assistent-registeret.

Fortsettelses-runden kunne ikke avgjøre A02/A08 m.fl. fordi modellene hermet
anmeldersjangeren. Her måles de samme listene mot tekst modellene skrev i
sitt naturlige assistentregister (generate_assistant.py). I tillegg testes
frasene som ble strøket i tidligere runder, og de mest overrepresenterte
n-grammene i registeret rapporteres.

Baseline-forbehold: NoReC er anmeldelser, ikke assistentsvar. Ord som er
sjeldne i anmeldelser, kan være vanlige i normal bruksprosa; wordfreq-zipf
brukes derfor som andre baseline for enkeltord, og høyeste av de to teller.

Kjør: .venv/bin/python bench/assistant_ratio.py > bench/report_assistant.md
"""

from __future__ import annotations

import gzip
import json
import sys
from collections import Counter
from pathlib import Path

import wordfreq

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from stillint.rules import load_rules  # noqa: E402

from llm_ratio import EPS, base_lookup, lookup, ngram_counts  # noqa: E402

BENCH = Path(__file__).resolve().parent
BASELINE = BENCH / "data" / "baseline_nb.json.gz"
ASSISTANT = BENCH / "data" / "llm_assistant.jsonl"

PRESENCE_RULES = ["A02_stilord_nb", "A03_skiltfraser", "A08_oppblast",
                  "A09_smisk", "A10_metaforsubstantiv", "D03_vag_kilde",
                  "E01_kalker", "E06_preposisjonskalker"]
# Fraser strøket i tidligere runder: får de comeback i assistentregisteret?
STRICKEN = ["med andre ord", "alt i alt", "kort sagt", "til syvende og sist",
            "når det kommer til", "i form av", "uten tvil", "i dagens samfunn"]
KEEP_RATIO = 3.0
MIN_COUNT = 3   # lite korpus: senk kravet, men rapporter antall


def human_pm(phrase: str, base: dict) -> float:
    pm = base_lookup(phrase, base) / base["tokens"] * 1e6
    if " " not in phrase:
        zipf = wordfreq.zipf_frequency(phrase, "nb")
        pm = max(pm, 10 ** (zipf - 3) if zipf else 0.0)
    return pm


def main() -> None:
    base = json.load(gzip.open(BASELINE, "rt"))
    rows = [json.loads(ln) for ln in ASSISTANT.read_text().splitlines()]
    uni, bi, tri, total = ngram_counts([r["text"] for r in rows])
    models = sorted({r["model"] for r in rows})

    print("# Presenslistene mot assistent-registeret")
    print()
    print(f"Materiale: {len(rows)} assistentsvar fra {len(models)} modeller "
          f"({total/1000:.0f}k token) i sjangrene spørsmål/e-post/varsel/råd.")
    print(f"Menneskelig baseline: NoReC ({base['tokens']/1e6:.1f} mill. token) "
          "og wordfreq nb (høyeste teller for enkeltord).")
    print()

    config = load_rules()

    def table(entries: list[str], heading: str) -> None:
        print(f"## {heading}")
        print()
        print("| ord/frase | assistent/mill. | antall | menneske/mill. | ratio | dom |")
        print("| --- | --- | --- | --- | --- | --- |")
        for phrase in entries:
            count = lookup(phrase, uni, bi, tri)
            llm_pm = count / total * 1e6
            h_pm = human_pm(phrase, base)
            ratio = (llm_pm + EPS) / (h_pm + EPS)
            if ratio >= KEEP_RATIO and count >= MIN_COUNT:
                verdict = "**BEHOLD**"
            elif count == 0:
                verdict = "ikke sett (0 treff)"
            else:
                verdict = "svak"
            print(f"| {phrase} | {llm_pm:.1f} | {count} | {h_pm:.2f} | {ratio:.1f}x | {verdict} |")
        print()

    for rule_id in PRESENCE_RULES:
        rule = config.by_id(rule_id)
        if rule and rule.words:
            table(rule.words, rule_id)
    table(STRICKEN, "Tidligere strøkne fraser")

    print("## Mest overrepresenterte n-gram i assistentregisteret")
    print()
    for name, counter, key, min_c in (("Bigram", bi, "bigrams", 5), ("Trigram", tri, "trigrams", 4)):
        print(f"### {name}")
        print()
        print("| n-gram | antall | assistent/mill. | menneske/mill. | ratio |")
        print("| --- | --- | --- | --- | --- |")
        cands = []
        for gram, count in counter.items():
            if count < min_c:
                continue
            llm_pm = count / total * 1e6
            h_pm = base[key].get(gram, 0) / base["tokens"] * 1e6
            ratio = (llm_pm + EPS) / (h_pm + EPS)
            if ratio >= 10:
                cands.append((ratio, gram, count, llm_pm, h_pm))
        for ratio, gram, count, llm_pm, h_pm in sorted(cands, reverse=True)[:25]:
            print(f"| {gram} | {count} | {llm_pm:.1f} | {h_pm:.2f} | {ratio:.0f}x |")
        print()


if __name__ == "__main__":
    main()
