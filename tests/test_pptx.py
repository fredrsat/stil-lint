import asyncio

import pytest

pptx_lib = pytest.importorskip("pptx")

from stillint.engine import Engine  # noqa: E402
from stillint.pptx_check import check_deck, extract_slides  # noqa: E402


def build_deck(path):
    from pptx import Presentation
    from pptx.util import Inches

    prs = Presentation()
    layout = prs.slide_layouts[1]  # tittel + innhold

    s1 = prs.slides.add_slide(layout)
    s1.shapes.title.text = "Kvartalsrapport Q3"
    s1.placeholders[1].text = ("Salget økte 12 % til 4,2 mill. kr\n"
                               "Tre nye kunder i Bergen\nLevering i snitt 2,1 dager")
    s1.notes_slide.notes_text_frame.text = (
        "Si at hovedtallet er 12 % vekst, drevet av avtalen med Vestkraft i august.")

    s2 = prs.slides.add_slide(layout)
    s2.shapes.title.text = "En Sømløs Og Banebrytende Reise"
    s2.placeholders[1].text = ("Vår sømløse og banebrytende plattform\n"
                               "Skreddersydd og helhetlig verdiskaping\n"
                               "Nøkkelen til synergi")
    s2.notes_slide.notes_text_frame.text = (
        "Det er viktig å merke seg at dette er nøkkelen til suksess. Håper dette hjelper!")

    meta = prs.slides.add_slide(prs.slide_layouts[5])
    meta.shapes.title.text = "AGENT-META"
    tb = meta.shapes.add_textbox(Inches(1), Inches(2), Inches(4), Inches(2))
    tb.text_frame.text = "sømløs banebrytende metadata som ikke skal lintes"

    prs.save(str(path))
    return path


def test_extract_slides(tmp_path):
    deck = build_deck(tmp_path / "deck.pptx")
    slides = extract_slides(deck)
    assert len(slides) == 3
    assert slides[0].title == "Kvartalsrapport Q3"
    assert "12 %" in slides[0].body
    assert "Vestkraft" in slides[0].notes
    assert slides[2].skipped  # AGENT-META hoppes over


def test_check_deck_flags_slop_slide(tmp_path):
    deck = build_deck(tmp_path / "deck.pptx")
    report = asyncio.run(check_deck(deck, mode="fast", engine=Engine(bank_path=tmp_path / "b.db")))
    assert report.verdict == "revise"
    deck_rules = {(f["rule"], f.get("slide")) for f in report.deck_result["findings"]}
    assert ("A02_stilord_nb", 2) in deck_rules          # stilord på slide 2
    assert ("B07_title_case_no", None) in deck_rules or any(
        r == "B07_title_case_no" for r, _ in deck_rules)
    assert all(s != 1 for r, s in deck_rules if s)      # den rene sliden flagges ikke
    notes_rules = {f["rule"] for f in report.notes_result["findings"]}
    assert "A04_chatbotrester" in notes_rules            # "Håper dette hjelper!" i notatene


def test_clean_deck_passes(tmp_path):
    from pptx import Presentation

    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[1])
    s.shapes.title.text = "Salget økte 12 % i tredje kvartal"
    s.placeholders[1].text = "4,2 mill. kr omsetning\nTre nye kunder i Bergen"
    path = tmp_path / "clean.pptx"
    prs.save(str(path))

    report = asyncio.run(check_deck(path, mode="fast", engine=Engine(bank_path=tmp_path / "b.db")))
    assert report.deck_result["findings"] == []


def _payload_from_deck(deck):
    return [{"number": s.number, "title": s.title, "body": s.body, "notes": s.notes}
            for s in extract_slides(deck)]


def test_check_slides_matches_check_deck(tmp_path):
    from stillint.pptx_check import check_slides, slides_from_payload

    deck = build_deck(tmp_path / "deck.pptx")
    engine = Engine(bank_path=tmp_path / "b.db")
    via_file = asyncio.run(check_deck(deck, mode="fast", engine=engine))
    via_text = asyncio.run(check_slides(slides_from_payload(_payload_from_deck(deck)),
                                        mode="fast", engine=engine))
    assert via_text.verdict == via_file.verdict == "revise"
    key = lambda r: sorted((f["rule"], f.get("slide"), f.get("p")) for f in r["findings"])  # noqa: E731
    assert key(via_text.deck_result) == key(via_file.deck_result)
    assert key(via_text.notes_result) == key(via_file.notes_result)
    assert [s.skipped for s in via_text.slides] == [False, False, True]  # AGENT-META via payload


def test_slides_from_payload_aliases_and_hidden():
    from stillint.pptx_check import slides_from_payload

    slides = slides_from_payload([
        {"n": 3, "text": "Punkt A\nPunkt B", "title": "Tittel"},
        {"body": "Skjult", "hidden": True},
        "bare en streng",
    ])
    assert [s.number for s in slides] == [3, 2, 3]
    assert slides[0].body == "Punkt A\nPunkt B" and slides[0].title == "Tittel"
    assert slides[1].skipped and not slides[0].skipped
    assert slides[2].body == "bare en streng"


def test_hidden_slide_is_skipped(tmp_path):
    from pptx import Presentation

    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[1])
    s.shapes.title.text = "Synlig"
    s.placeholders[1].text = "Salget økte 12 %"
    h = prs.slides.add_slide(prs.slide_layouts[1])
    h.shapes.title.text = "En Sømløs Og Banebrytende Reise"
    h.placeholders[1].text = "sømløs banebrytende synergi"
    h._element.set("show", "0")
    path = tmp_path / "hidden.pptx"
    prs.save(str(path))

    slides = extract_slides(path)
    assert [sl.skipped for sl in slides] == [False, True]
    report = asyncio.run(check_deck(path, mode="fast", engine=Engine(bank_path=tmp_path / "b.db")))
    assert report.deck_result["findings"] == []


def test_mcp_check_slides_tool(tmp_path):
    from stillint import server

    deck = build_deck(tmp_path / "deck.pptx")
    out = asyncio.run(server.check_slides(_payload_from_deck(deck)))
    assert out["verdict"] == "revise"
    assert out["slides_checked"] == [1, 2] and out["slides_skipped"] == [3]
    assert any(f.get("slide") == 2 for f in out["deck"]["findings"])

    missing = asyncio.run(server.check_pptx("/mnt/user-data/outputs/finnes-ikke.pptx"))
    assert "check_slides" in missing["hint"]


def test_extract_reads_tables_and_groups(tmp_path):
    from pptx import Presentation
    from pptx.util import Inches

    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[5])
    s.shapes.title.text = "Tall for kvartalet"
    tbl = s.shapes.add_table(2, 2, Inches(1), Inches(2), Inches(6), Inches(1)).table
    tbl.cell(0, 0).text = "Omsetning"
    tbl.cell(0, 1).text = "4,2 mill. kr"
    tbl.cell(1, 0).text = "Sømløs og banebrytende synergi"
    tbl.cell(1, 1).text = "Nøkkelen til vekst"
    grp = s.shapes.add_group_shape()
    box = grp.shapes.add_textbox(Inches(1), Inches(4), Inches(4), Inches(1))
    box.text_frame.text = "Tekst inne i en gruppe"
    prs.save(str(tmp_path / "t.pptx"))

    slides = extract_slides(tmp_path / "t.pptx")
    assert slides[0].title == "Tall for kvartalet"
    assert "Omsetning | 4,2 mill. kr" in slides[0].body
    assert "Tekst inne i en gruppe" in slides[0].body

    report = asyncio.run(check_deck(tmp_path / "t.pptx", mode="fast",
                                    engine=Engine(bank_path=tmp_path / "b.db")))
    assert any(f["rule"] == "A02_stilord_nb" and f.get("slide") == 1
               for f in report.deck_result["findings"])


def test_skill_script_matches_server_extraction(tmp_path):
    """Skriptet i skills/ er frittstående og må gi samme payload som extract_slides."""
    import json
    import subprocess
    import sys
    from pathlib import Path

    script = Path(__file__).resolve().parents[1] / "skills/stil-lint-pptx/scripts/extract_slides.py"
    deck = build_deck(tmp_path / "deck.pptx")
    ext = json.loads(subprocess.check_output([sys.executable, str(script), str(deck)]))
    srv = extract_slides(deck)
    assert [(e["number"], e["title"], e["body"], e["notes"]) for e in ext] == \
           [(s.number, s.title, s.body, s.notes) for s in srv]
    assert ext[2]["hidden"] is False and ext[2]["title"] == "AGENT-META"


def _notes_deck(tmp_path, long_notes: bool):
    from pptx import Presentation

    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[1])
    s.shapes.title.text = "Salget økte 12 % i tredje kvartal"
    s.placeholders[1].text = "4,2 mill. kr omsetning\nTre nye kunder i Bergen"
    note = ("Si at veksten kom fra avtalen med Vestkraft i august. " * (12 if long_notes else 1)).strip()
    s.notes_slide.notes_text_frame.text = note
    path = tmp_path / "notes.pptx"
    prs.save(str(path))
    return path


def test_unrequested_notes_flagged(tmp_path):
    deck = _notes_deck(tmp_path, long_notes=False)
    engine = Engine(bank_path=tmp_path / "b.db")

    r = asyncio.run(check_deck(deck, mode="fast", engine=engine, notes_requested=False))
    f = next(f for f in r.notes_result["findings"] if f["rule"] == "F07_ubestilte_notater")
    assert "slide 1" in f["evidence"] and not f.get("advisory")
    assert r.verdict != "pass"

    r = asyncio.run(check_deck(deck, mode="fast", engine=engine, notes_requested=True))
    assert not any(f["rule"].startswith("F07") or f["rule"].startswith("F08")
                   for f in r.notes_result["findings"])

    r = asyncio.run(check_deck(deck, mode="fast", engine=engine))  # ukjent: korte notater, ingen F07
    assert not any(f["rule"].startswith("F0") for f in r.notes_result["findings"])


def test_long_notes_advisory(tmp_path):
    deck = _notes_deck(tmp_path, long_notes=True)
    r = asyncio.run(check_deck(deck, mode="fast", engine=Engine(bank_path=tmp_path / "b.db")))
    f = next(f for f in r.notes_result["findings"] if f["rule"] == "F08_lange_notater")
    assert f["advisory"] and f["slide"] == 1 and "ord i notatet" in f["evidence"]
    assert r.verdict in ("pass", "pass_with_notes")  # råd stopper ikke dekket


def test_mcp_check_slides_notes_requested(tmp_path):
    from stillint import server

    out = asyncio.run(server.check_slides(
        [{"number": 1, "title": "Salget økte 12 %", "body": "Tre nye kunder i Bergen",
          "notes": "Nevn Vestkraft-avtalen."}], notes_requested=False))
    assert any(f["rule"] == "F07_ubestilte_notater" for f in out["notes"]["findings"])
