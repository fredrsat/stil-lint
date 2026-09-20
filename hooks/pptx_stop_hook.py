#!/usr/bin/env python
"""Claude Code Stop-hook: stilsjekk nylig endrede .pptx-filer.

Finner .pptx endret siste 30 min under sesjonens cwd, kjører stil-lint
(slide-profil) og gir Claude beskjed EN gang per deck-versjon (innholdshash)
hvis dommen er revise. Ellers helt stille. Mønster fra slopcheck-jev:
advar, ikke blokker permanent.

Modus: fast (lokalt) med mindre TYPESAFE_API_KEY er satt i miljøet, da full.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
import time
from pathlib import Path

STATE_FILE = Path.home() / ".stil-lint" / "pptx_hook_state.json"
MAX_AGE_SECONDS = 30 * 60
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__"}


def recent_decks(root: Path) -> list[Path]:
    now = time.time()
    decks = []
    for path in root.rglob("*.pptx"):
        if any(part in SKIP_DIRS or part.startswith("~$") for part in path.parts):
            continue
        try:
            if now - path.stat().st_mtime <= MAX_AGE_SECONDS:
                decks.append(path)
        except OSError:
            continue
    return decks


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    root = Path(payload.get("cwd") or os.getcwd())

    decks = recent_decks(root)
    if not decks:
        return

    try:
        from stillint.engine import Engine
        from stillint.pptx_check import check_deck, format_report
    except ImportError:
        return  # stil-lint ikke installert i dette miljøet: aldri blokker

    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
        except Exception:
            state = {}

    mode = "full" if os.environ.get("TYPESAFE_API_KEY") else "fast"
    engine = Engine()
    reports = []
    for deck in decks:
        digest = hashlib.sha256(deck.read_bytes()).hexdigest()[:16]
        if state.get(str(deck)) == digest:
            continue  # alt varslet for denne versjonen
        try:
            report = asyncio.run(check_deck(deck, mode=mode, engine=engine))
        except Exception:
            continue
        state[str(deck)] = digest
        if report.verdict == "revise":
            reports.append(format_report(report))

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state))

    if reports:
        print(json.dumps({
            "decision": "block",
            "reason": (
                "stil-lint fant AI-aktige stiltrekk i presentasjonen(e) du nettopp "
                "endret. Vurder hvert funn med hintet som står ved det; bruk "
                "keep_if-unntakene der de gjelder. Rett det som bør rettes i "
                "pptx-filen, eller forklar kort hvorfor funnene skal stå. Denne "
                "advarselen kommer bare en gang per versjon av filen.\n\n"
                + "\n\n".join(reports)
            ),
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
