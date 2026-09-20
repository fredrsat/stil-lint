import asyncio

import pytest

from stillint.bank import PhraseBank
from stillint.engine import Engine
from stillint.gate import apply_gate
from stillint.lex import Finding
from stillint.rules import Profile, load_rules

CONFIG = load_rules()


def find(rule="X", sev=2, p=1.0, layer="regex", advisory=False):
    return Finding(rule=rule, layer=layer, scope="paragraph", paragraph=0,
                   p=p, severity=sev, hint="", advisory=advisory)


def test_gate_pass_when_clean():
    r = apply_gate(CONFIG, Profile("t"), [], {}, [])
    assert r.verdict == "pass" and r.score == 1.0


def test_gate_revise_on_severe():
    r = apply_gate(CONFIG, Profile("t"), [find(sev=3)], {}, [])
    assert r.verdict == "revise"


def test_gate_pass_with_notes_after_max_rounds():
    r = apply_gate(CONFIG, Profile("t"), [find(sev=3)], {}, [], round_num=2, max_rounds=2)
    assert r.verdict == "pass_with_notes"


def test_gate_advisory_does_not_block():
    r = apply_gate(CONFIG, Profile("t"), [find(advisory=True)], {}, [])
    assert r.verdict == "pass"


def test_gate_jev_threshold_from_profile():
    profile = Profile("t", thresholds={"X": 0.9})
    r = apply_gate(CONFIG, profile, [find(layer="jev", p=0.8)], {}, [])
    assert r.findings == [] and r.verdict == "pass"


def test_gate_missing_positive():
    profile = Profile("t", required_positives=["G01_konkret_detalj"])
    r = apply_gate(CONFIG, profile, [], {"G01_konkret_detalj": 0.2}, [])
    assert r.verdict == "revise" and r.missing


def test_engine_fast_mode(tmp_path):
    engine = Engine(bank_path=tmp_path / "bank.db")
    result = asyncio.run(engine.check_text(
        "Hei!\nOppdatering: vi har en **banebrytende** og **sømløs** oppdatering!",
        genre="varsel", channel="push", mode="fast",
    ))
    rules = {f["rule"] for f in result["findings"]}
    assert "F02_hilsen_i_varsel" in rules
    assert "F06_etikettapning" in rules
    assert "B11_markdown_i_rentekst" in rules
    assert result["verdict"] == "revise"
    assert result["meta"]["mode"] == "fast"


def test_engine_clean_alert_passes(tmp_path):
    engine = Engine(bank_path=tmp_path / "bank.db")
    result = asyncio.run(engine.check_text(
        "Bussen 505 er 8 minutter forsinket. Ny avgang 07:50 fra Solligata.",
        genre="varsel", channel="push", mode="fast",
    ))
    assert result["verdict"] == "pass"


def test_engine_keeps_paragraph_index_zero(tmp_path):
    engine = Engine(bank_path=tmp_path / "bank.db")
    result = asyncio.run(engine.check_text(
        "Det er viktig å merke seg at bussen går 07:42.", genre="sakprosa", mode="fast",
    ))
    f = next(f for f in result["findings"] if f["rule"] == "A03_skiltfraser")
    assert f["paragraph"] == 0


def test_phrase_bank_f05(tmp_path):
    engine = Engine(bank_path=tmp_path / "bank.db")
    msg = "Bussen 505 er forsinket i dag, ny avgang klokka 07:50 fra Solligata som vanlig."
    engine.bank_add("buss-agent", msg)
    result = asyncio.run(engine.check_text(msg, genre="varsel", channel="push",
                                           mode="fast", agent_id="buss-agent"))
    assert "F05_gjentatt_formulering" in {f["rule"] for f in result["findings"]}


def test_phrase_bank_overlap(tmp_path):
    bank = PhraseBank(tmp_path / "b.db")
    bank.add("a", "en helt vanlig melding om bussen som går fra byen i morgen tidlig")
    assert bank.overlap("a", "en helt vanlig melding om bussen som går fra byen i morgen tidlig") == 1.0
    assert bank.overlap("a", "noe helt annet innhold uten felles formuleringer i det hele tatt her") < 0.2
    assert bank.overlap("annen-agent", "en helt vanlig melding om bussen som går fra byen i morgen tidlig") == 0.0


def test_all_profile_references_resolve():
    from stillint.rules import list_profiles, load_profile
    ids = {r.id for r in CONFIG.rules}
    for name in list_profiles():
        p = load_profile(name)
        for ref in p.rules_off + p.rules_advisory + p.required_positives + list(p.thresholds):
            assert ref in ids, f"{name}: ukjent regel {ref}"


def test_jev_mode_without_key_reports_error(tmp_path, monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    engine = Engine(bank_path=tmp_path / "bank.db")
    result = asyncio.run(engine.check_text("En tekst.", mode="full"))
    assert "jev_error" in result["meta"]
