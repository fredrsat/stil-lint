"""Steg 5, analyse: LLM-siden av frekvensratioen (slop-forensics-metoden).

Sammenligner egen-generert norsk LLM-tekst (generate_pairs.py) mot den
menneskelige baselinen (build_baseline.py) og gjør tre ting:

1. Fullfører ordlistevalideringen: ratio per ord/frase i A02/E01 m.fl.
   Dokumentets regel: behold ord med høy ratio og nok forekomster, dropp
   resten uansett hvor AI-aktige de føles.
2. Oppdager nye kandidater: n-gram som er mest overrepresentert i LLM-tekst,
   per modellfamilie og samlet (fingeravtrykkene er familiespesifikke).
3. Parvis separasjon (evalueringsplanens punkt 3): kjører mode=fast på
   menneskets og modellens fortsettelse av samme åpning og måler forskjellen.

Kjør: .venv/bin/python bench/llm_ratio.py > bench/report_llm_ratio.md
"""

from __future__ import annotations

import asyncio
import gzip
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from stillint.engine import Engine  # noqa: E402
from stillint.rules import load_rules  # noqa: E402

BENCH = Path(__file__).resolve().parent
BASELINE = BENCH / "data" / "baseline_nb.json.gz"
PAIRS = BENCH / "data" / "llm_pairs.jsonl"

TOKEN = re.compile(r"[a-zæøåéA-ZÆØÅÉ]+")
LIST_RULES = ["A02_stilord_nb", "A03_skiltfraser", "A05_forsterkere", "A08_oppblast",
              "A10_metaforsubstantiv", "D03_vag_kilde", "E01_kalker", "E06_preposisjonskalker"]
EPS = 0.1          # glatting i ratio
KEEP_RATIO = 3.0   # behold: minst 3x overrepresentert
DROP_RATIO = 2.0   # under 2x: stryk
MIN_LLM_COUNT = 5


def tokens(text: str) -> list[str]:
    return [t.lower() for t in TOKEN.findall(text)]


def ngram_counts(texts: list[str]) -> tuple[Counter, Counter, Counter, int]:
    uni, bi, tri = Counter(), Counter(), Counter()
    total = 0
    for text in texts:
        toks = tokens(text)
        total += len(toks)
        uni.update(toks)
        bi.update(" ".join(toks[i:i + 2]) for i in range(len(toks) - 1))
        tri.update(" ".join(toks[i:i + 3]) for i in range(len(toks) - 2))
    return uni, bi, tri, total


def lookup(phrase: str, uni: Counter, bi: Counter, tri: Counter) -> int:
    toks = phrase.lower().split()
    if len(toks) == 1:
        return uni[toks[0]]
    if len(toks) == 2:
        return bi[" ".join(toks)]
    if len(toks) == 3:
        return tri[" ".join(toks)]
    counts = [tri[" ".join(toks[i:i + 3])] for i in range(len(toks) - 2)]
    return min(counts) if counts else 0


def base_lookup(phrase: str, base: dict) -> int:
    toks = phrase.lower().split()
    table = {1: "unigrams", 2: "bigrams", 3: "trigrams"}.get(len(toks))
    if table is None:
        counts = [base["trigrams"].get(" ".join(toks[i:i + 3]), 0) for i in range(len(toks) - 2)]
        return min(counts) if counts else 0
    return base[table].get(" ".join(toks), 0)


async def main() -> None:
    base = json.load(gzip.open(BASELINE, "rt"))
    rows = [json.loads(ln) for ln in PAIRS.read_text().splitlines()]
    by_model: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        by_model[row["model"]].append(row["llm_text"])
    all_texts = [r["llm_text"] for r in rows]
    uni, bi, tri, llm_total = ngram_counts(all_texts)
    per_model_counts = {m: ngram_counts(t) for m, t in by_model.items()}

    print("# LLM-siden av frekvensratioen")
    print()
    print(f"Materiale: {len(rows)} fortsettelser fra {len(by_model)} modeller "
          f"({llm_total/1000:.0f}k token). Baseline: {base['source']} "
          f"({base['tokens']/1e6:.1f} mill. token).")
    print()
    print("**Viktig forbehold om register:** materialet er *fortsettelser av"
          " anmeldelser* (Reinhart-metoden). Modellene hermer sjangeren, så"
          " assistent-registerets stilord (banebrytende, i dagens samfunn,"
          " chatbot-fraser) forekommer naturlig nok ikke. STRYK i tabellen under"
          " betyr derfor \"ikke overrepresentert i denne sjangeren\", ikke at"
          " ordet er friskmeldt i agent- og assistenttekst. Presenslistene"
          " (A02, A08 m.fl.) må valideres separat med assistent-oppgaver"
          " (svar på spørsmål, skriv en melding) før de strykes. BEHOLD-dommer"
          " og nye kandidater er derimot gyldige: de er overrepresentert til"
          " tross for at modellene prøver å treffe menneskelig sjanger.")
    print()

    # 1. Ordlistevalidering
    config = load_rules()
    print("## Ordlistevalidering: endelig ratio")
    print()
    print(f"Behold: ratio >= {KEEP_RATIO} og >= {MIN_LLM_COUNT} LLM-forekomster. "
          f"Stryk: ratio < {DROP_RATIO}. Ellers: usikker (trenger mer data).")
    print()
    print("| regel | ord/frase | LLM/mill. | menneske/mill. | ratio | dom |")
    print("| --- | --- | --- | --- | --- | --- |")
    for rule_id in LIST_RULES:
        rule = config.by_id(rule_id)
        if rule is None or not rule.words:
            continue
        for phrase in rule.words:
            lc = lookup(phrase, uni, bi, tri)
            bc = base_lookup(phrase, base)
            llm_pm = lc / llm_total * 1e6
            base_pm = bc / base["tokens"] * 1e6
            ratio = (llm_pm + EPS) / (base_pm + EPS)
            if ratio >= KEEP_RATIO and lc >= MIN_LLM_COUNT:
                verdict = "**BEHOLD**"
            elif ratio < DROP_RATIO:
                verdict = "STRYK"
            else:
                verdict = "usikker"
            print(f"| {rule_id} | {phrase} | {llm_pm:.1f} | {base_pm:.2f} | {ratio:.1f}x | {verdict} |")
    print()

    # 2. Oppdagelse av nye kandidater
    def discover(llm_counter: Counter, base_table: dict, total: int, min_count: int) -> list[tuple]:
        out = []
        for gram, count in llm_counter.items():
            if count < min_count:
                continue
            llm_pm = count / total * 1e6
            base_pm = base_table.get(gram, 0) / base["tokens"] * 1e6
            ratio = (llm_pm + EPS) / (base_pm + EPS)
            if ratio >= 5.0:
                out.append((ratio, gram, count, llm_pm, base_pm))
        return sorted(out, reverse=True)

    print("## Nye kandidater: mest overrepresenterte n-gram (samlet)")
    print()
    for name, counter, table, min_c in (("Unigram", uni, base["unigrams"], 15),
                                        ("Bigram", bi, base["bigrams"], 10),
                                        ("Trigram", tri, base["trigrams"], 8)):
        print(f"### {name}")
        print()
        print("| n-gram | LLM-antall | LLM/mill. | menneske/mill. | ratio |")
        print("| --- | --- | --- | --- | --- |")
        for ratio, gram, count, llm_pm, base_pm in discover(counter, table, llm_total, min_c)[:25]:
            print(f"| {gram} | {count} | {llm_pm:.1f} | {base_pm:.2f} | {ratio:.0f}x |")
        print()

    print("## Familiespesifikke fingeravtrykk (topp bigram per modell)")
    print()
    for model, (mu, mb, mt, mtotal) in sorted(per_model_counts.items()):
        tops = discover(mb, base["bigrams"], mtotal, 5)[:8]
        grams = ", ".join(f"{g} ({r:.0f}x)" for r, g, *_ in tops)
        print(f"- **{model}** ({mtotal/1000:.0f}k token): {grams}")
    print()

    # 3. Parvis separasjon i mode=fast
    engine = Engine()
    stats: dict[str, dict] = defaultdict(lambda: {"n": 0, "human_f": 0, "llm_f": 0,
                                                  "human_hit": 0, "llm_hit": 0})
    for row in rows:
        res_h = await engine.check_text(row["human_rest"], genre="sakprosa", mode="fast")
        res_l = await engine.check_text(row["llm_text"], genre="sakprosa", mode="fast")
        key = f"{row['model']} ({row['variant']})"
        s = stats[key]
        s["n"] += 1
        s["human_f"] += len(res_h["findings"])
        s["llm_f"] += len(res_l["findings"])
        s["human_hit"] += bool(res_h["findings"])
        s["llm_hit"] += bool(res_l["findings"])

    print("## Parvis separasjon, mode=fast (uten Jev)")
    print()
    print("Samme åpning; menneskets fortsettelse mot modellens. Funn per tekst og")
    print("andel tekster med minst ett funn.")
    print()
    print("| modell (variant) | n | funn/tekst menneske | funn/tekst LLM | flagget menneske | flagget LLM |")
    print("| --- | --- | --- | --- | --- | --- |")
    for key, s in sorted(stats.items()):
        print(f"| {key} | {s['n']} | {s['human_f']/s['n']:.2f} | {s['llm_f']/s['n']:.2f} "
              f"| {s['human_hit']/s['n']:.0%} | {s['llm_hit']/s['n']:.0%} |")
    print()
    print("Merk: mode=fast måler bare regex/stat-lagene. Jev-laget (skjønn) er der")
    print("hovedskillet ventes; det måles i seeded-fault-evalueringen (steg 8).")


if __name__ == "__main__":
    asyncio.run(main())
