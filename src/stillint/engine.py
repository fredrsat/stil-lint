"""Orkestrering av lagene 0-5 og JSON-svaret fra del 7 i researchdokumentet."""

from __future__ import annotations

import os
import time
from dataclasses import asdict
from pathlib import Path

from . import jev as jev_layer
from .bank import OVERLAP_THRESHOLD, PhraseBank
from .gate import apply_gate, active_rules
from .lex import Finding, run_lex
from .preprocess import preprocess
from .rules import RuleConfig, load_profile, load_rules
from .stat import run_stat


class Engine:
    def __init__(self, rules_dir: Path | None = None, bank_path: Path | str | None = None):
        self.config: RuleConfig = load_rules(rules_dir) if rules_dir else load_rules()
        self._bank_path = bank_path

    def _bank(self) -> PhraseBank:
        return PhraseBank(self._bank_path) if self._bank_path else PhraseBank()

    async def check_text(
        self,
        text: str,
        genre: str = "sakprosa",
        channel: str | None = None,
        lang: str | None = None,
        mode: str = "fast",
        agent_id: str | None = None,
        round_num: int = 1,
        max_rounds: int = 2,
    ) -> dict:
        t0 = time.monotonic()
        profile = load_profile(genre)
        pre = preprocess(text, lang=lang)
        rules = active_rules(self.config, profile, genre)

        findings: list[Finding] = []
        findings += run_lex(pre, rules, channel)
        findings += run_stat(pre, rules, channel)

        # Lag 3: frasebank (bare når agent_id er oppgitt)
        if agent_id:
            bank_rule = self.config.by_id("F05_gjentatt_formulering")
            if bank_rule and bank_rule.id not in profile.rules_off:
                overlap = self._bank().overlap(agent_id, pre.cleaned)
                if overlap > OVERLAP_THRESHOLD:
                    findings.append(Finding(
                        rule=bank_rule.id, layer="bank", scope="document", paragraph=None,
                        p=round(overlap, 2), severity=bank_rule.severity, hint=bank_rule.hint,
                    ))

        positives: dict[str, float] = {}
        no_judgment: list[str] = []
        jev_calls = 0
        jev_error: str | None = None

        if mode == "full":
            try:
                jev_findings, positives, no_judgment, jev_calls = await jev_layer.run_jev(
                    pre, self.config, genre, rules
                )
                findings += jev_findings
            except jev_layer.JevError as exc:
                jev_error = str(exc)

        result = apply_gate(self.config, profile, findings, positives, no_judgment,
                            round_num=round_num, max_rounds=max_rounds)

        response = {
            "verdict": result.verdict,
            "score": result.score,
            "round": round_num,
            "max_rounds": max_rounds,
            "findings": [
                {"id": f"f{i}", **{k: v for k, v in asdict(f).items()
                                   if v is not None
                                   or k in ("p", "rule", "layer", "scope", "severity", "hint", "paragraph")}}
                for i, f in enumerate(result.findings, 1)
            ],
            "positives": result.positives,
            "missing": result.missing,
            "no_judgment": result.no_judgment,
            "meta": {
                "model": (os.environ.get(jev_layer.MODEL_ENV, self.config.model)
                          if mode == "full" else None),
                "mode": mode,
                "ms": int((time.monotonic() - t0) * 1000),
                "jev_calls": jev_calls,
                "lang": pre.lang,
                "genre": genre,
                "paragraphs": len(pre.paragraphs),
            },
        }
        if jev_error:
            response["meta"]["jev_error"] = jev_error
        return response

    def bank_add(self, agent_id: str, text: str) -> dict:
        pre = preprocess(text)
        n = self._bank().add(agent_id, pre.cleaned)
        return {"agent_id": agent_id, "shingles_added": n}
