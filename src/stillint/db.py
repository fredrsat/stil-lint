"""Felles SQLite-tilkobling som tåler parallelle kall.

busy_timeout settes FØR journal_mode: WAL-byttet krever eksklusiv lås og
feilet ellers med "database is locked" når flere tilkoblinger åpnet samtidig.
Taper vi likevel kappløpet om selve byttet, er det greit - WAL er persistent
per databasefil, så vinneren har alt satt den.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def connect(path: Path | str) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30, check_same_thread=False)
    conn.execute("PRAGMA busy_timeout=30000")
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.OperationalError:
        pass
    return conn
