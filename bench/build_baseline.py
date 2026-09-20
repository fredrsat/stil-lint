"""Bygg frekvensbaseline fra NoReC (steg 4 i arbeidsrekkefølgen).

Teller unigram, bigram og trigram over bokmålsdelen av NoReC og lagrer
resultatet som bench/data/baseline_nb.json.gz. Brukes av
validate_wordlists.py og senere av slop-forensics-ratioen mot LLM-tekst.

Kjør: .venv/bin/python bench/build_baseline.py
"""

from __future__ import annotations

import gzip
import json
import re
import sys
from collections import Counter
from pathlib import Path

BENCH = Path(__file__).resolve().parent
NOREC = BENCH / "data" / "norec" / "data"
OUT = BENCH / "data" / "baseline_nb.json.gz"

TOKEN = re.compile(r"[a-zæøåéA-ZÆØÅÉ]+")
PRUNE_AT = 3_000_000  # dropp engangs-n-gram når tabellen blir så stor


def tokens(text: str) -> list[str]:
    return [t.lower() for t in TOKEN.findall(text)]


def main() -> None:
    meta = json.load(open(NOREC / "metadata.json"))
    nb_ids = {f"{int(k):06d}" for k, v in meta.items()
              if v.get("language") == "nb" and (v.get("year") or 0) <= 2019}

    uni: Counter = Counter()
    bi: Counter = Counter()
    tri: Counter = Counter()
    docs = 0
    total = 0

    for split in ("train", "dev", "test"):
        for path in sorted((NOREC / split).glob("*.txt")):
            if path.stem not in nb_ids:
                continue
            toks = tokens(path.read_text(errors="ignore"))
            docs += 1
            total += len(toks)
            uni.update(toks)
            bi.update(" ".join(toks[i:i + 2]) for i in range(len(toks) - 1))
            tri.update(" ".join(toks[i:i + 3]) for i in range(len(toks) - 2))
            for counter in (bi, tri):
                if len(counter) > PRUNE_AT:
                    for key in [k for k, c in counter.items() if c == 1]:
                        del counter[key]
            if docs % 5000 == 0:
                print(f"  {docs} dokumenter, {total/1e6:.1f} mill. token", file=sys.stderr)

    out = {
        "source": "NoReC (ltgoslo/norec), bokmål, t.o.m. 2019",
        "docs": docs,
        "tokens": total,
        "unigrams": {w: c for w, c in uni.items() if c >= 3},
        "bigrams": {w: c for w, c in bi.items() if c >= 5},
        "trigrams": {w: c for w, c in tri.items() if c >= 5},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUT, "wt") as fh:
        json.dump(out, fh, ensure_ascii=False)
    print(f"Skrev {OUT}: {docs} dok, {total/1e6:.1f} mill. token, "
          f"{len(out['unigrams'])} unigram, {len(out['bigrams'])} bigram, {len(out['trigrams'])} trigram")


if __name__ == "__main__":
    main()
