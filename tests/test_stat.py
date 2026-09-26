from stillint.preprocess import preprocess
from stillint.rules import load_rules
from stillint.stat import lix, run_stat

RULES = load_rules().rules


def rule_ids(text, channel=None):
    pre = preprocess(text)
    return {f.rule for f in run_stat(pre, RULES, channel)}


def test_c08_uniform_rhythm():
    text = ("Verktøyet gjør arbeidet mye enklere for alle brukere. "
            "Systemet gir de ansatte en bedre oversikt over alt. "
            "Løsningen sparer bedriften for både tid og penger. "
            "Plattformen hjelper kundene med å finne frem raskt.")
    assert "C08_ensartet_rytme" in rule_ids(text)


def test_c08_varied_rhythm_ok():
    text = ("Bussen var full. Jeg måtte stå hele veien fra sentrum til skolen, "
            "klemt mellom to sekker. Sjåføren kjørte forbi to holdeplasser uten å stoppe. "
            "Rart. I morgen sykler jeg heller, selv om det regner.")
    assert "C08_ensartet_rytme" not in rule_ids(text)


def test_c11_nominalization():
    text = ("Gjennomføringen av evalueringen forutsetter en kartlegging av "
            "implementeringen og en vurdering av organiseringen, samt en "
            "utredning av finansieringen og en avklaring av ansvarsfordelingen "
            "før iverksettelsen av omstillingen kan påbegynnes i virksomheten.")
    assert "C11_nominalisering" in rule_ids(text)


def test_f01_long_alert():
    text = ("Bussen er forsinket. Den nye avgangen er 07:52. "
            "Det er fortsatt mulig å rekke skolen. Husk å ta med gymtøy i dag.")
    assert "F01_for_langt_varsel" in rule_ids(text, channel="push")
    assert "F01_for_langt_varsel" not in rule_ids("Bussen er forsinket. Ny avgang 07:52.", channel="push")


def test_b05_structure_in_short_text():
    text = "# Status\n\n- punkt en\n- punkt to\n\nKort tekst."
    assert "B05_struktur_vs_lengde" in rule_ids(text)


def test_b15_suspicious_unicode():
    assert "B15_mistenkelig_unicode" in rule_ids("Ordet st\u0101r med macron her.")
    assert "B15_mistenkelig_unicode" in rule_ids("Usynlig\u200btegn i ordet.")
    assert "B15_mistenkelig_unicode" in rule_ids("Myk\u00adbindestrek i ordet.")
    assert "B15_mistenkelig_unicode" not in rule_ids(
        "Vanlig norsk tekst \u2013 med tankestrek og \u00abanf\u00f8rselstegn\u00bb.")


def test_b15_names_the_characters():
    from stillint.preprocess import preprocess
    from stillint.stat import run_stat
    pre = preprocess("To\u202fusynlige\u202ftegn og \u0101 her.")
    findings = [f for f in run_stat(pre, RULES, None) if f.rule == "B15_mistenkelig_unicode"]
    assert len(findings) == 1
    assert "U+202F smalt hardt mellomrom x2" in findings[0].evidence
    assert "macron" in findings[0].evidence


def test_lix_sane():
    easy = "Bussen kommer klokka åtte. Vi rekker skolen fint. Husk sekken din."
    hard = ("Kommunestyret vedtok i går kveld en omfattende reguleringsplan for "
            "områdene rundt jernbanestasjonen, med tilhørende konsekvensutredninger.")
    assert lix(easy) < 15 < lix(hard)
