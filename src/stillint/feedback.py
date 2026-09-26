"""Lagring av tilbakemeldinger for kalibrering (record_feedback).

`riktig_men_greit` er dataene som lar alvorlighet læres per sjanger.
"""

from __future__ import annotations

import time
from pathlib import Path

from . import db

DEFAULT_DB = Path.home() / ".stil-lint" / "feedback.db"
VERDICTS = ("riktig", "feil", "riktig_men_greit")


def record(rule: str, verdict: str, genre: str | None = None,
           comment: str | None = None, db_path: Path | str = DEFAULT_DB) -> dict:
    if verdict not in VERDICTS:
        raise ValueError(f"verdict må være en av {VERDICTS}")
    conn = db.connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS feedback ("
        " rule TEXT NOT NULL, verdict TEXT NOT NULL, genre TEXT, comment TEXT, ts REAL NOT NULL)"
    )
    conn.execute(
        "INSERT INTO feedback (rule, verdict, genre, comment, ts) VALUES (?, ?, ?, ?, ?)",
        (rule, verdict, genre, comment, time.time()),
    )
    conn.commit()
    row = conn.execute("SELECT COUNT(*) FROM feedback WHERE rule = ?", (rule,)).fetchone()
    conn.close()
    return {"rule": rule, "verdict": verdict, "total_feedback_for_rule": row[0]}
