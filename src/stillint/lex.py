"""Lag 1: regex og ordlister. Lokalt, gratis, ingen tekst forlater maskinen."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .preprocess import PreprocessedText
from .rules import Rule


@dataclass
class Finding:
    rule: str
    layer: str
    scope: str
    paragraph: int | None       # None for dokumentfunn
    p: float                    # 1.0 for regex/stat (deterministisk), Jev-sannsynlighet ellers
    severity: int
    hint: str
    keep_if: str | None = None
    evidence: str | None = None
    count: int = 0
    advisory: bool = False


def _matches(rule: Rule, text: str) -> list[str]:
    rx = rule.compiled()
    if rx is None:
        return []
    return [m if isinstance(m, str) else m[0] for m in rx.findall(text)]


def _over_limit(rule: Rule, count: int, words: int) -> bool:
    if count == 0:
        return False
    if rule.max_per_1000 is not None:
        # Tetthetsregler krever minst to treff: ett stilord i et kort avsnitt
        # er ikke et mønster.
        return count >= 2 and words > 0 and count / words * 1000 > rule.max_per_1000
    return count > rule.max_count


def run_lex(pre: PreprocessedText, rules: list[Rule], channel: str | None) -> list[Finding]:
    findings: list[Finding] = []
    for rule in rules:
        if rule.layer != "regex" or pre.lang not in rule.lang:
            continue
        if rule.channels is not None and channel not in rule.channels:
            continue
        if rule.scope == "document":
            hits = _matches(rule, pre.cleaned)
            if _over_limit(rule, len(hits), pre.word_count):
                findings.append(_finding(rule, None, hits))
        else:
            for para in pre.paragraphs:
                if para.is_heading:
                    continue
                hits = _matches(rule, para.text)
                para_words = len(re.findall(r"\S+", para.text))
                if _over_limit(rule, len(hits), para_words):
                    findings.append(_finding(rule, para.index, hits))
    return findings


def _finding(rule: Rule, paragraph: int | None, hits: list[str]) -> Finding:
    return Finding(
        rule=rule.id,
        layer="regex",
        scope=rule.scope,
        paragraph=paragraph,
        p=1.0,
        severity=rule.severity,
        hint=rule.hint,
        keep_if=rule.keep_if,
        evidence=", ".join(dict.fromkeys(h.strip() for h in hits[:5])) or None,
        count=len(hits),
        advisory=rule.advisory,
    )
