"""Lagring og oppsummering av tilbakemeldinger for kalibrering (record_feedback).

`riktig_men_greit` er dataene som lar alvorlighet læres per sjanger: en regel
som ofte er riktig men grei, bør bli råd (advisory) i den sjangeren. `feil`
er falske positiver og peker på regler som bør strammes eller fjernes.
"""

from __future__ import annotations

import time
from pathlib import Path

from . import db

DEFAULT_DB = Path.home() / ".stil-lint" / "feedback.db"
VERDICTS = ("riktig", "feil", "riktig_men_greit")

# Terskler for anbefalingene i summary(). Krever et minimum av dommer før
# noe sies, så én enkelt "feil" ikke feller en regel.
MIN_VOTES = 5
FP_LIMIT = 0.3          # andel feil over dette: regelen bør strammes
SOFT_LIMIT = 0.5        # andel riktig_men_greit over dette: bør bli råd i sjangeren


def _open(db_path: Path | str):
    conn = db.connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS feedback ("
        " rule TEXT NOT NULL, verdict TEXT NOT NULL, genre TEXT, comment TEXT,"
        " ts REAL NOT NULL, evidence TEXT)"
    )
    cols = {row[1] for row in conn.execute("PRAGMA table_info(feedback)")}
    if "evidence" not in cols:  # databaser fra før kolonnen fantes
        conn.execute("ALTER TABLE feedback ADD COLUMN evidence TEXT")
    return conn


def record(rule: str, verdict: str, genre: str | None = None,
           comment: str | None = None, evidence: str | None = None,
           db_path: Path | str = DEFAULT_DB) -> dict:
    if verdict not in VERDICTS:
        raise ValueError(f"verdict må være en av {VERDICTS}")
    conn = _open(db_path)
    conn.execute(
        "INSERT INTO feedback (rule, verdict, genre, comment, ts, evidence)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (rule, verdict, genre, comment, time.time(), evidence),
    )
    conn.commit()
    row = conn.execute("SELECT COUNT(*) FROM feedback WHERE rule = ?", (rule,)).fetchone()
    conn.close()
    return {"rule": rule, "verdict": verdict, "total_feedback_for_rule": row[0]}


def summary(db_path: Path | str = DEFAULT_DB, genre: str | None = None) -> list[dict]:
    """Dommer per regel og sjanger, med andeler og en anbefaling.

    Returnerer én rad per (rule, genre), sortert med høyest feil-andel først.
    """
    conn = _open(db_path)
    where, params = ("WHERE genre = ?", (genre,)) if genre else ("", ())
    rows = conn.execute(
        "SELECT rule, genre, verdict, COUNT(*) FROM feedback"
        f" {where} GROUP BY rule, genre, verdict", params,
    ).fetchall()
    conn.close()

    table: dict[tuple[str, str | None], dict[str, int]] = {}
    for rule, g, verdict, n in rows:
        table.setdefault((rule, g), {v: 0 for v in VERDICTS})[verdict] += n

    out = []
    for (rule, g), counts in table.items():
        total = sum(counts.values())
        fp = counts["feil"] / total
        soft = counts["riktig_men_greit"] / total
        if total < MIN_VOTES:
            advice = f"for få dommer ({total} < {MIN_VOTES})"
        elif fp > FP_LIMIT:
            advice = "stram regelen eller fjern den: for mange falske positiver"
        elif soft > SOFT_LIMIT:
            advice = "gjør regelen til råd (rules_advisory) i denne sjangeren"
        else:
            advice = "behold"
        out.append({"rule": rule, "genre": g, "total": total, **counts,
                    "feil_andel": round(fp, 2), "greit_andel": round(soft, 2),
                    "advice": advice})
    out.sort(key=lambda r: (-r["feil_andel"], -r["greit_andel"], r["rule"]))
    return out


def format_summary(rows: list[dict]) -> str:
    if not rows:
        return "Ingen tilbakemeldinger registrert."
    lines = [f"{'regel':34s} {'sjanger':10s} {'n':>3s} {'riktig':>6s} {'feil':>5s} {'greit':>5s}  anbefaling"]
    for r in rows:
        lines.append(f"{r['rule']:34s} {(r['genre'] or '-'):10s} {r['total']:3d} "
                     f"{r['riktig']:6d} {r['feil']:5d} {r['riktig_men_greit']:5d}  {r['advice']}")
    return "\n".join(lines)
