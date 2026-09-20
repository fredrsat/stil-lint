"""Lag 5: gate. Terskler, sjangerprofil og alvorlighetsvekting.

Policy ligger her, i kode - modellen blir aldri spurt om et menneske bør bry
seg (prinsipp lånt fra slopcheck-jev).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .lex import Finding
from .rules import Profile, Rule, RuleConfig

POSITIVE_MIN = 0.4   # under dette regnes et positivt signal som fraværende


@dataclass
class GateResult:
    verdict: str                      # pass | revise | pass_with_notes
    score: float
    findings: list[Finding] = field(default_factory=list)
    positives: dict[str, float] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    no_judgment: list[str] = field(default_factory=list)


def active_rules(config: RuleConfig, profile: Profile, genre: str | None) -> list[Rule]:
    out = []
    for rule in config.rules:
        if genre and genre in rule.genres_off:
            continue
        if rule.id in profile.rules_off:
            continue
        out.append(rule)
    return out


def apply_gate(
    config: RuleConfig,
    profile: Profile,
    findings: list[Finding],
    positives: dict[str, float],
    no_judgment: list[str],
    round_num: int = 1,
    max_rounds: int = 2,
) -> GateResult:
    kept: list[Finding] = []
    for f in findings:
        threshold = profile.thresholds.get(f.rule, config.threshold)
        if f.layer == "jev" and f.p < threshold:
            continue
        if f.rule in profile.rules_advisory:
            f.advisory = True
        kept.append(f)
    kept.sort(key=lambda f: (-f.severity, -f.p))

    # Score: 1.0 minus alvorlighetsvektede funn, pluss krav om positive signaler.
    penalty = sum(profile.severity_weights.get(f.severity, 0.12) * f.p
                  for f in kept if not f.advisory)
    score = max(0.0, 1.0 - penalty)

    missing = []
    for rule_id in profile.required_positives:
        p = positives.get(rule_id)
        if p is not None and p < POSITIVE_MIN:
            missing.append(f"{rule_id} under {POSITIVE_MIN} (p={p:.2f})")

    blocking = [f for f in kept if not f.advisory]
    has_severe = any(f.severity >= 3 for f in blocking)

    if not blocking and not missing:
        verdict = "pass"
    elif round_num >= max_rounds:
        verdict = "pass_with_notes"
    elif has_severe or score < profile.pass_score or missing:
        verdict = "revise"
    else:
        verdict = "pass_with_notes"

    return GateResult(
        verdict=verdict,
        score=round(score, 2),
        findings=kept,
        positives={k: round(v, 2) for k, v in positives.items()},
        missing=missing,
        no_judgment=no_judgment,
    )
