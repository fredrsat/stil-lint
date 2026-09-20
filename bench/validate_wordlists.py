"""Valider ordlistene i rules/lex.yaml mot menneskelig baseline (del 8).

Dette er den menneskelige halvdelen av frekvensratioen: hvor vanlig er hvert
ord/frase i tekst skrevet av mennesker før LLM-æraen (NoReC t.o.m. 2019,
pluss wordfreq nb-snapshot)? Et "AI-ord" som er vanlig hos mennesker, er et
dårlig tilstedeværelsestegn uansett hvor AI-aktig det føles - dokumentets
regel: "Dropp resten, uansett hvor AI-aktige de føles."

LLM-halvdelen (overrepresentasjon i egen-generert norsk LLM-tekst) kommer i
steg 5 og trengs før noe ord får STRYK/BEHOLD-status endelig.

Kjør: .venv/bin/python bench/validate_wordlists.py > bench/report_wordlists.md
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import wordfreq

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from stillint.rules import load_rules  # noqa: E402

BENCH = Path(__file__).resolve().parent
BASELINE = BENCH / "data" / "baseline_nb.json.gz"

# Regler med norske ordlister som skal valideres.
LIST_RULES = ["A02_stilord_nb", "A03_skiltfraser", "A05_forsterkere", "A08_oppblast",
              "A10_metaforsubstantiv", "D03_vag_kilde", "E01_kalker", "E06_preposisjonskalker"]

# Grov klassifisering av frekvens per million token i menneskelig tekst.
COMMON = 10.0    # hyppig hos mennesker: ubrukelig som tilstedeværelsestegn
MODERATE = 1.0   # middels: bare brukbar i tetthetsregler


def per_million(phrase: str, base: dict) -> float:
    toks = phrase.lower().split()
    table = {1: "unigrams", 2: "bigrams", 3: "trigrams"}.get(len(toks))
    if table is None:
        # lengre fraser: bruk sjeldneste innholds-trigram som overslag
        counts = [base["trigrams"].get(" ".join(toks[i:i + 3]), 0)
                  for i in range(len(toks) - 2)]
        count = min(counts) if counts else 0
    else:
        count = base[table].get(" ".join(toks), 0)
    return count / base["tokens"] * 1e6


def main() -> None:
    base = json.load(gzip.open(BASELINE, "rt"))
    config = load_rules()

    print("# Ordlistevalidering mot menneskelig baseline")
    print()
    print(f"Baseline: {base['source']}, {base['docs']} dokumenter, "
          f"{base['tokens'] / 1e6:.1f} mill. token. wordfreq nb-snapshot (før 2022).")
    print()
    print("Dette er den menneskelige halvdelen av frekvensratioen. Endelig")
    print("STRYK/BEHOLD krever LLM-siden (steg 5). Foreløpig tolkning:")
    print(f"- **hyppig** (> {COMMON}/mill. hos mennesker): dårlig tegn, kandidat for stryking")
    print(f"- **middels** ({MODERATE}-{COMMON}/mill.): bare brukbar i tetthetsregel, ikke enkeltfunn")
    print(f"- **sjelden** (< {MODERATE}/mill.): lovende tegn hvis LLM-siden viser overrepresentasjon")
    print()

    for rule_id in LIST_RULES:
        rule = config.by_id(rule_id)
        if rule is None or not rule.words:
            continue
        print(f"## {rule_id}")
        print()
        print("| ord/frase | NoReC per mill. | wordfreq zipf | vurdering |")
        print("| --- | --- | --- | --- |")
        rows = []
        for phrase in rule.words:
            pm = per_million(phrase, base)
            zipf = (wordfreq.zipf_frequency(phrase, "nb")
                    if " " not in phrase else None)
            # zipf 4.0 ≈ 10/mill., 3.0 ≈ 1/mill.
            level = max(pm, 10 ** ((zipf or 0) - 3)) if zipf else pm
            verdict = ("hyppig - kandidat for stryking" if level > COMMON
                       else "middels - kun tetthet" if level > MODERATE
                       else "sjelden - lovende")
            rows.append((level, phrase, pm, zipf, verdict))
        for level, phrase, pm, zipf, verdict in sorted(rows, reverse=True):
            z = f"{zipf:.2f}" if zipf is not None else "-"
            print(f"| {phrase} | {pm:.2f} | {z} | {verdict} |")
        print()


if __name__ == "__main__":
    main()
