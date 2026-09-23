"""Lag 4: Jev (TypeSafe System One).

Ett dokumentkall pluss ett kall per avsnitt, sendt samtidig (del 3, regel 10-12).
Cache nøkles på hash av tekst + eksakt spørsmålstekst + modell; teksten selv
lagres aldri (mønster fra snifftest).

Krever TYPESAFE_API_KEY i miljøet. Verifisert mot docs.typesafe.ai 2026-09-20:
POST {state, model, questions:{id:{type:"noul", instructions, criteria}}} ->
{answers:{id:{noul: p}}}.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
import sqlite3
import time
from pathlib import Path

import httpx

from .lex import Finding
from .preprocess import PreprocessedText
from .rules import Rule, RuleConfig

# Direkte mot TypeSafe som standard. Sett TYPESAFE_BASE_URL=https://openrouter.ai/api
# for å gå via OpenRouter (samme Decisions API, OpenRouter-nøkkel som Bearer).
BASE_URL_ENV = "TYPESAFE_BASE_URL"
DEFAULT_BASE_URL = "https://api.typesafe.ai"
API_KEY_ENV = "TYPESAFE_API_KEY"
MODEL_ENV = "TYPESAFE_MODEL"


CACHE_DB = Path.home() / ".stil-lint" / "jev-cache.db"
CACHE_TTL = 14 * 24 * 3600
MAX_RETRIES = 4


class JevError(RuntimeError):
    pass


def api_key() -> str | None:
    return os.environ.get(API_KEY_ENV)


def api_url() -> str:
    return os.environ.get(BASE_URL_ENV, DEFAULT_BASE_URL).rstrip("/") + "/v1/systemone"


class _Cache:
    def __init__(self, path: Path = CACHE_DB):
        path.parent.mkdir(parents=True, exist_ok=True)
        # WAL + busy_timeout: parallelle kall (flere samtidige check_text/check_pptx)
        # deler denne databasen og skal vente på hverandre, ikke feile med "locked".
        self.conn = sqlite3.connect(path, timeout=30, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=30000")
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS answers (key TEXT PRIMARY KEY, p REAL NOT NULL, ts REAL NOT NULL)"
        )
        self.conn.commit()

    @staticmethod
    def key(text: str, question: str, model: str) -> str:
        return hashlib.sha256(f"{model}\x00{question}\x00{text}".encode()).hexdigest()

    def get(self, key: str) -> float | None:
        row = self.conn.execute(
            "SELECT p, ts FROM answers WHERE key = ?", (key,)
        ).fetchone()
        if row and time.time() - row[1] < CACHE_TTL:
            return row[0]
        return None

    def put(self, key: str, p: float) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO answers (key, p, ts) VALUES (?, ?, ?)",
            (key, p, time.time()),
        )
        self.conn.commit()


def _question_payload(rule: Rule) -> dict:
    q: dict = {"type": "noul", "instructions": rule.what.strip()}
    if rule.not_for:
        q["instructions"] += f"\n\nSkal IKKE flagges: {rule.not_for.strip()}"
    if rule.criteria:
        q["criteria"] = {str(k): str(v) for k, v in rule.criteria.items()}
    return q


async def _call(client: httpx.AsyncClient, state: str, questions: dict[str, dict], model: str) -> dict[str, float]:
    payload = {"state": state, "model": model, "questions": questions}
    delay = 1.0
    for attempt in range(MAX_RETRIES):
        resp = await client.post(
            api_url(),
            json=payload,
            headers={"Authorization": f"Bearer {api_key()}"},
            timeout=30.0,
        )
        if resp.status_code in (429, 500, 502, 503) and attempt < MAX_RETRIES - 1:
            await asyncio.sleep(delay)
            delay *= 2
            continue
        if resp.status_code != 200:
            raise JevError(f"Jev-API svarte {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        return {qid: ans["noul"] for qid, ans in data.get("answers", {}).items() if "noul" in ans}
    raise JevError("Jev-API: tomt for forsøk")


async def run_jev(
    pre: PreprocessedText,
    config: RuleConfig,
    genre: str | None,
    active_rules: list[Rule],
) -> tuple[list[Finding], dict[str, float], list[str], int]:
    """Returnerer (funn, positive-signaler, ingen-vurdering-liste, antall API-kall)."""
    if not api_key():
        raise JevError(f"{API_KEY_ENV} er ikke satt. Kjør mode=fast, eller sett nøkkelen.")

    jev_rules = [r for r in active_rules if r.layer == "jev" and pre.lang in r.lang]
    doc_rules = [r for r in jev_rules if r.scope == "document"]
    para_rules = [r for r in jev_rules if r.scope == "paragraph"]
    # Overskrifter er med: en slidetittel som "Ikke bare X - også Y" er nettopp
    # det C01 skal se. Ordgulvet (5) siler bare bort fragmenter Jev ikke kan lese.
    prose = list(pre.paragraphs)

    # Modell-ID kan overstyres per miljø: OpenRouter bruker "jev-1.13"/"jev-latest",
    # direkte-API-et "jev-1.13.0". Cache-nøkkelen bruker samme resolverte ID.
    model = os.environ.get(MODEL_ENV, config.model)

    cache = _Cache()
    lo, hi = config.no_judgment_band
    findings: list[Finding] = []
    positives: dict[str, float] = {}
    no_judgment: list[str] = []
    in_band: set[str] = set()
    calls = 0

    async with httpx.AsyncClient() as client:
        tasks: list[tuple[str | None, int | None, list[Rule], dict[str, dict], asyncio.Task | None]] = []

        def prepare(state: str, rules: list[Rule], paragraph: int | None):
            nonlocal calls
            questions, cached = {}, {}
            for rule in rules:
                key = cache.key(state, rule.what or "", model)
                hit = cache.get(key)
                if hit is not None:
                    cached[rule.id] = hit
                else:
                    questions[rule.id] = _question_payload(rule)
            task = None
            if questions:
                task = asyncio.ensure_future(_call(client, state, questions, model))
                calls += 1
            tasks.append((state, paragraph, rules, cached, task))

        if doc_rules:
            prepare(pre.cleaned, doc_rules, None)
        for para in prose:
            words = len(re.findall(r"[\wæøåÆØÅ]+", para.text))
            if para_rules and words >= 5:
                prepare(para.text, para_rules, para.index)

        for state, paragraph, rules, answers, task in tasks:
            if task is not None:
                fresh = await task
                for rule in rules:
                    if rule.id in fresh:
                        cache.put(cache.key(state, rule.what or "", model), fresh[rule.id])
                answers = {**answers, **fresh}
            for rule in rules:
                p = answers.get(rule.id)
                if p is None:
                    continue
                if lo <= p <= hi:
                    no_judgment.append(rule.id)
                    in_band.add(rule.id)
                    continue
                if rule.positive:
                    # For positive signaler beholdes høyeste p over dokumentet.
                    positives[rule.id] = max(positives.get(rule.id, 0.0), p)
                elif p > hi:
                    findings.append(Finding(
                        rule=rule.id, layer="jev", scope=rule.scope, paragraph=paragraph,
                        p=round(p, 2), severity=rule.severity, hint=rule.hint,
                        keep_if=rule.keep_if, advisory=rule.advisory,
                    ))

    # Positive regler som svarte klart nei, rapporteres som lav p (gate-en avgjør
    # om det gir "missing"). Regler i ingen-vurdering-båndet holdes utenfor:
    # "kan ikke vurderes" er ikke det samme som "mangler".
    for rule in jev_rules:
        if rule.positive and rule.id not in positives and rule.id not in in_band:
            positives[rule.id] = 0.0

    return findings, positives, sorted(set(no_judgment)), calls
