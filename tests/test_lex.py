from stillint.lex import run_lex
from stillint.preprocess import preprocess
from stillint.rules import load_rules

CONFIG = load_rules()
RULES = CONFIG.rules


def rule_ids(text, channel=None, lang=None):
    pre = preprocess(text, lang=lang)
    return {f.rule for f in run_lex(pre, RULES, channel)}


def test_a02_stilord_density():
    text = ("Dette er en banebrytende og revolusjonerende løsning. Den er sømløs og "
            "helhetlig, et paradigmeskifte som gir verdifull innsikt.")
    assert "A02_stilord_nb" in rule_ids(text)


def test_a02_single_word_ok():
    text = ("Rapporten fra i fjor beskriver arbeidet som banebrytende. Resten av "
            "dokumentet handler om budsjettet for neste år, fordelt på tre poster "
            "og med en egen tabell for lønnsutgifter i kapittel fire, som styret "
            "vedtok i mars etter to runder med innspill fra avdelingene i Bergen "
            "og Trondheim, der de fleste kommentarene gjaldt reisekostnader.")
    assert "A02_stilord_nb" not in rule_ids(text)


def test_a04_chatbot():
    assert "A04_chatbotrester" in rule_ids("Her er oversikten du ba om. Håper dette hjelper!")


def test_b07_title_case():
    assert "B07_title_case_no" in rule_ids("# Fem Grunner Til Suksess\n\nInnhold her.")
    assert "B07_title_case_no" not in rule_ids("# Fem grunner til suksess\n\nInnhold her.")


def test_b11_markdown_only_in_plain_channels():
    text = "**Viktig:** bussen er forsinket."
    assert "B11_markdown_i_rentekst" in rule_ids(text, channel="push")
    assert "B11_markdown_i_rentekst" not in rule_ids(text, channel="epost")


def test_f02_greeting_in_push():
    assert "F02_hilsen_i_varsel" in rule_ids("Hei! Bussen er forsinket.", channel="push")
    assert "F02_hilsen_i_varsel" not in rule_ids("Bussen er forsinket 10 minutter.", channel="push")


def test_f06_label_opening():
    assert "F06_etikettapning" in rule_ids("Oppdatering: bussen kommer 07:42.", channel="push")


def test_b08_oxford_comma_only_in_lists():
    assert "B08_oxford_komma" in rule_ids("Vi kjøpte epler, pærer, og bananer.")
    # Komma foran "og" mellom helsetninger er korrekt norsk.
    assert "B08_oxford_komma" not in rule_ids("Han kom hjem, og hun dro på jobb.")


def test_d10_menu_ending():
    assert "D10_menyavslutning" in rule_ids("Leksene er ferdige. Vil du at jeg skal sette opp en plan?")


def test_e01_kalker():
    assert "E01_kalker" in rule_ids("På slutten av dagen er det innsatsen som teller.")


def test_english_wordlist_on_english_text():
    text = ("Let us delve into the rich tapestry of this vibrant landscape, "
            "a testament to the seamless interplay of robust and pivotal forces.")
    assert "A01_stilord_en" in rule_ids(text, lang="en")


def test_clean_paragraph_no_findings():
    text = ("Bussen til skolen går 07:42 fra Solligata. Ta med regnjakke, for "
            "det er meldt 4 mm regn mellom 08 og 10. Husk gymtøy i dag.")
    assert rule_ids(text, channel="push") == set()
