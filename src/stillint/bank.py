"""Lag 3: frasebank (F05). SQLite med shingles på 5-8 ord per agent.

Ideen er lånt fra unslopify: en agent som varierer ett fast mønster med et
annet fast mønster, avsløres bare av minne på tvers av meldinger.
Bare hasher lagres, aldri tekst.
"""

from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path

from . import db

SHINGLE_SIZE = 6
OVERLAP_THRESHOLD = 0.5
DEFAULT_DB = Path.home() / ".stil-lint" / "bank.db"


def _shingles(text: str, size: int = SHINGLE_SIZE) -> set[str]:
    words = re.findall(r"[\wæøåÆØÅ]+", text.lower())
    if len(words) < size:
        words = words + [""] * (size - len(words))
        return {hashlib.sha256(" ".join(words).encode()).hexdigest()[:16]}
    return {
        hashlib.sha256(" ".join(words[i:i + size]).encode()).hexdigest()[:16]
        for i in range(len(words) - size + 1)
    }


class PhraseBank:
    def __init__(self, db_path: Path | str = DEFAULT_DB):
        self.db_path = Path(db_path)
        self.conn = db.connect(self.db_path)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS shingles ("
            " agent_id TEXT NOT NULL, shingle TEXT NOT NULL, ts REAL NOT NULL,"
            " PRIMARY KEY (agent_id, shingle))"
        )
        self.conn.commit()

    def overlap(self, agent_id: str, text: str) -> float:
        """Andel av tekstens shingles som finnes i banken for denne agenten."""
        shingles = _shingles(text)
        if not shingles:
            return 0.0
        marks = ",".join("?" * len(shingles))
        row = self.conn.execute(
            f"SELECT COUNT(*) FROM shingles WHERE agent_id = ? AND shingle IN ({marks})",
            [agent_id, *shingles],
        ).fetchone()
        return row[0] / len(shingles)

    def add(self, agent_id: str, text: str) -> int:
        shingles = _shingles(text)
        now = time.time()
        self.conn.executemany(
            "INSERT OR REPLACE INTO shingles (agent_id, shingle, ts) VALUES (?, ?, ?)",
            [(agent_id, s, now) for s in shingles],
        )
        self.conn.commit()
        return len(shingles)

    def close(self) -> None:
        self.conn.close()
