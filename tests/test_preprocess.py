from stillint.preprocess import detect_lang, preprocess


def test_strips_front_matter_and_code():
    text = "---\ntitle: x\n---\nEt avsnitt med tekst.\n\n```python\nprint('delve tapestry')\n```\n\nNeste avsnitt."
    pre = preprocess(text)
    assert "delve" not in pre.cleaned
    assert "title" not in pre.cleaned
    assert len(pre.paragraphs) == 2


def test_strips_blockquotes():
    pre = preprocess("Egen tekst her.\n\n> sitert tekst med sømløs synergi\n\nMer egen tekst.")
    assert "sømløs" not in pre.cleaned


def test_detect_lang():
    assert detect_lang("Jeg vet ikke hva som skjer, men det er noe rart på gang.") == "nb"
    assert detect_lang("Eg veit ikkje kva som skjer, men det er noko rart på gang.") == "nn"
    assert detect_lang("The bus is delayed and it will not arrive before noon.") == "en"


def test_paragraph_kinds():
    pre = preprocess("# Overskrift\n\n- punkt en\n- punkt to\n\nVanlig avsnitt.")
    assert pre.paragraphs[0].is_heading
    assert pre.paragraphs[1].is_list
    assert not pre.paragraphs[2].is_heading
