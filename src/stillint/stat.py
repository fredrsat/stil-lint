"""Lag 2: statistiske mål. Lokalt, uten modell.

Implementert uten spaCy (heuristikker); med spaCy installert kan
nominaliserings- og passivmålene byttes til POS-baserte versjoner senere.
"""

from __future__ import annotations

import re
import statistics

from .lex import Finding
from .preprocess import PreprocessedText
from .rules import Rule

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÆØÅ«\"])")
CONNECTORS = ("dessuten", "i tillegg", "videre", "samtidig", "imidlertid", "derfor",
              "dermed", "følgelig", "på den annen side")
# Nominaliserings-heuristikk: avledningssuffikser på substantiv.
NOMINALIZATION = re.compile(r"\b\w{4,}(sjon|sjonen|sjoner|ering|eringen|else|elsen|het|heten)\b", re.IGNORECASE)

# Terskler. Tunes mot korpus i evalueringen (del 8); startverdier er konservative.
CV_THRESHOLD = 0.22          # C08: variasjonskoeffisient for setningslengde
MIN_SENTENCES_FOR_CV = 4
NOMINALIZATION_PER_100 = 6.0  # C11: per 100 ord
CONNECTOR_SHARE = 0.4         # A11: andel setninger som åpner med koblingsord
MIN_SENTENCES_FOR_CONNECTOR = 5
STRUCTURE_WORD_LIMIT = 120    # B05: struktur i tekst kortere enn dette
CHANNEL_MAX_SENTENCES = {"push": 2, "sms": 3, "varsel": 2}


def sentences(text: str) -> list[str]:
    return [s for s in SENTENCE_SPLIT.split(text.strip()) if s]


def lix(text: str) -> float:
    words = re.findall(r"[\wæøåÆØÅ]+", text)
    if not words:
        return 0.0
    sents = max(1, len(sentences(text)))
    long_words = sum(1 for w in words if len(w) > 6)
    return len(words) / sents + 100 * long_words / len(words)


def run_stat(pre: PreprocessedText, rules: list[Rule], channel: str | None) -> list[Finding]:
    by_id = {r.id: r for r in rules if r.layer == "stat"}
    findings: list[Finding] = []

    def emit(rule_id: str, paragraph: int | None, evidence: str) -> None:
        rule = by_id.get(rule_id)
        if rule is None or pre.lang not in rule.lang:
            return
        if rule.channels is not None and channel not in rule.channels:
            return
        findings.append(Finding(
            rule=rule.id, layer="stat", scope=rule.scope, paragraph=paragraph,
            p=1.0, severity=rule.severity, hint=rule.hint, keep_if=rule.keep_if,
            evidence=evidence, advisory=rule.advisory,
        ))

    prose = [p for p in pre.paragraphs if not p.is_heading and not p.is_list]

    # C08: ensartet setningslengde per avsnitt
    for para in prose:
        lengths = [len(re.findall(r"\S+", s)) for s in sentences(para.text)]
        if len(lengths) >= MIN_SENTENCES_FOR_CV and statistics.mean(lengths) > 0:
            cv = statistics.pstdev(lengths) / statistics.mean(lengths)
            if cv < CV_THRESHOLD:
                emit("C08_ensartet_rytme", para.index,
                     f"setningslengder {lengths}, variasjonskoeffisient {cv:.2f}")

    # C11: nominaliseringstetthet per avsnitt
    for para in prose:
        words = len(re.findall(r"\S+", para.text))
        if words >= 30:
            n = len(NOMINALIZATION.findall(para.text))
            per_100 = n / words * 100
            if per_100 > NOMINALIZATION_PER_100:
                emit("C11_nominalisering", para.index, f"{n} nominaliseringer på {words} ord")

    # A11: koblingsord i setningsstart, hele dokumentet
    all_sents = [s for p in prose for s in sentences(p.text)]
    if len(all_sents) >= MIN_SENTENCES_FOR_CONNECTOR:
        openers = sum(1 for s in all_sents if s.lower().startswith(CONNECTORS))
        if openers / len(all_sents) > CONNECTOR_SHARE:
            emit("A11_koblingsord", None, f"{openers} av {len(all_sents)} setninger")

    # B05: overskrifter/lister i kort tekst
    structure = sum(1 for p in pre.paragraphs if p.is_heading or p.is_list)
    if structure >= 2 and pre.word_count < STRUCTURE_WORD_LIMIT:
        emit("B05_struktur_vs_lengde", None,
             f"{structure} strukturelementer i tekst på {pre.word_count} ord")

    # F01: varsellengde
    max_sents = CHANNEL_MAX_SENTENCES.get(channel or "")
    if max_sents is not None:
        n = len(sentences(pre.cleaned))
        if n > max_sents:
            emit("F01_for_langt_varsel", None, f"{n} setninger, kanalgrense {max_sents}")

    return findings
