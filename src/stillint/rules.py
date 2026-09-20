"""Regelmodell og lasting av rules/*.yaml.

Formatet er lånt fra snifftest og slopcheck-jev (del 3 i researchdokumentet):
spørsmålstekst i YAML, terskler og policy i kode/profil.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

RULES_DIR = Path(__file__).resolve().parents[2] / "rules"
PROFILES_DIR = Path(__file__).resolve().parents[2] / "profiles"


@dataclass
class Rule:
    id: str
    layer: str                      # regex | stat | jev | bank
    scope: str = "paragraph"        # paragraph | document
    lang: list[str] = field(default_factory=lambda: ["nb", "nn", "en"])
    severity: int = 2               # 1 kosmetisk, 2 merkbar, 3 ødelegger tilliten
    genres_off: list[str] = field(default_factory=list)
    channels: list[str] | None = None   # bare aktiv i disse kanalene (None = alle)
    advisory: bool = False          # teller ikke i score, bare rapporteres
    # regex-lag
    pattern: str | None = None
    words: list[str] = field(default_factory=list)
    max_count: int = 0              # funn når antall treff > max_count
    max_per_1000: float | None = None  # tetthetsregel: treff per 1000 ord
    # jev-lag
    what: str | None = None
    not_for: str | None = None
    criteria: dict | None = None
    positive: bool = False          # G-gruppen: teller FOR teksten
    # felles
    hint: str = ""
    keep_if: str | None = None

    _compiled: re.Pattern | None = field(default=None, repr=False, compare=False)

    def compiled(self) -> re.Pattern | None:
        if self._compiled is None:
            if self.pattern:
                self._compiled = re.compile(self.pattern, re.MULTILINE)
            elif self.words:
                alts = "|".join(re.escape(w) for w in sorted(self.words, key=len, reverse=True))
                self._compiled = re.compile(rf"(?<![\wæøåÆØÅ])(?:{alts})(?![\wæøåÆØÅ])", re.IGNORECASE)
        return self._compiled


@dataclass
class RuleConfig:
    model: str = "jev-1.13.0"
    threshold: float = 0.7
    no_judgment_band: tuple[float, float] = (0.40, 0.60)
    rules: list[Rule] = field(default_factory=list)

    def by_id(self, rule_id: str) -> Rule | None:
        return next((r for r in self.rules if r.id == rule_id), None)


@dataclass
class Profile:
    name: str
    rules_off: list[str] = field(default_factory=list)
    rules_advisory: list[str] = field(default_factory=list)
    thresholds: dict[str, float] = field(default_factory=dict)
    max_words: int | None = None
    pass_score: float = 0.75
    required_positives: list[str] = field(default_factory=list)
    severity_weights: dict[int, float] = field(default_factory=lambda: {1: 0.05, 2: 0.12, 3: 0.30})


def load_rules(rules_dir: Path = RULES_DIR) -> RuleConfig:
    config = RuleConfig()
    known = {f.name for f in Rule.__dataclass_fields__.values() if not f.name.startswith("_")}
    for path in sorted(rules_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text()) or {}
        config.model = data.get("model", config.model)
        config.threshold = data.get("threshold", config.threshold)
        if "no_judgment_band" in data:
            config.no_judgment_band = tuple(data["no_judgment_band"])
        for raw in data.get("rules", []):
            fields = {k: v for k, v in raw.items() if k in known}
            config.rules.append(Rule(**fields))
    seen: set[str] = set()
    for rule in config.rules:
        if rule.id in seen:
            raise ValueError(f"Duplisert regel-ID: {rule.id}")
        seen.add(rule.id)
    return config


def load_profile(name: str, profiles_dir: Path = PROFILES_DIR) -> Profile:
    path = profiles_dir / f"{name}.yaml"
    if not path.exists():
        return Profile(name=name)
    data = yaml.safe_load(path.read_text()) or {}
    profile = Profile(name=name)
    for key in ("rules_off", "rules_advisory", "thresholds", "max_words", "pass_score", "required_positives"):
        if key in data:
            setattr(profile, key, data[key])
    if "severity_weights" in data:
        profile.severity_weights = {int(k): float(v) for k, v in data["severity_weights"].items()}
    return profile


def list_profiles(profiles_dir: Path = PROFILES_DIR) -> list[str]:
    return sorted(p.stem for p in profiles_dir.glob("*.yaml"))
