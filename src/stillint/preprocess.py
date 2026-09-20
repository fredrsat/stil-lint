"""Lag 0: forbehandling.

Fjerner front matter, kodeblokker og sitater før analyse (regel 14 i
researchdokumentet: tekst som omtaler et kjennetegn, blir flagget for å
inneholde det). Deler i avsnitt og gjetter språk.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

FRONT_MATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
FENCED_CODE_RE = re.compile(r"^(```|~~~).*?^\1\s*$", re.DOTALL | re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
BLOCKQUOTE_RE = re.compile(r"^>.*$", re.MULTILINE)

# Stoppord for språkgjetting. Nynorsk og bokmål skilles på markørord.
_NB = {"ikke", "jeg", "en", "et", "hva", "hvordan", "noe", "mye", "være", "blitt", "fra", "også", "å", "og", "det", "som", "på", "med", "har", "til", "av", "om"}
_NN = {"ikkje", "eg", "ein", "ei", "eit", "kva", "korleis", "noko", "mykje", "vere", "blitt", "frå", "òg", "å", "og", "det", "som", "på", "med", "har", "til", "av", "om"}
_EN = {"the", "and", "is", "of", "to", "in", "that", "it", "for", "with", "was", "not", "this", "are", "you"}
_NN_MARKERS = {"ikkje", "eg", "ein", "eit", "kva", "korleis", "noko", "mykje", "frå", "òg", "vere", "berre", "nokre", "anten"}


@dataclass
class Paragraph:
    index: int
    text: str
    is_heading: bool = False
    is_list: bool = False


@dataclass
class PreprocessedText:
    original: str
    cleaned: str
    paragraphs: list[Paragraph] = field(default_factory=list)
    lang: str = "nb"  # nb | nn | en
    word_count: int = 0
    removed_blocks: int = 0


def detect_lang(text: str) -> str:
    words = re.findall(r"[a-zA-ZæøåÆØÅ']+", text.lower())
    if not words:
        return "nb"
    nb = sum(1 for w in words if w in _NB)
    nn = sum(1 for w in words if w in _NN)
    en = sum(1 for w in words if w in _EN)
    if en > max(nb, nn):
        return "en"
    # nb- og nn-listene overlapper mye; markørordene avgjør.
    if any(w in _NN_MARKERS for w in words) and nn >= nb:
        return "nn"
    return "nb"


def split_paragraphs(text: str) -> list[Paragraph]:
    paragraphs: list[Paragraph] = []
    for i, raw in enumerate(re.split(r"\n\s*\n", text)):
        chunk = raw.strip()
        if not chunk:
            continue
        lines = chunk.splitlines()
        is_heading = bool(re.match(r"^#{1,6}\s", chunk)) and len(lines) == 1
        is_list = all(re.match(r"^\s*(?:[-*+•]|\d+[.)])\s", ln) for ln in lines)
        paragraphs.append(Paragraph(index=len(paragraphs), text=chunk, is_heading=is_heading, is_list=is_list))
    return paragraphs


def preprocess(text: str, lang: str | None = None) -> PreprocessedText:
    removed = 0
    cleaned = text
    if FRONT_MATTER_RE.match(cleaned):
        cleaned = FRONT_MATTER_RE.sub("", cleaned, count=1)
        removed += 1
    cleaned, n = FENCED_CODE_RE.subn("", cleaned)
    removed += n
    cleaned, n = BLOCKQUOTE_RE.subn("", cleaned)
    removed += n
    cleaned = INLINE_CODE_RE.sub("KODE", cleaned)

    paragraphs = split_paragraphs(cleaned)
    body = "\n\n".join(p.text for p in paragraphs)
    return PreprocessedText(
        original=text,
        cleaned=body,
        paragraphs=paragraphs,
        lang=lang or detect_lang(body),
        word_count=len(re.findall(r"\S+", body)),
        removed_blocks=removed,
    )
