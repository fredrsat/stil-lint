import sqlite3

from stillint import feedback


def test_record_and_summary(tmp_path):
    dbp = tmp_path / "fb.db"
    for _ in range(4):
        feedback.record("A02_stilord_nb", "feil", genre="slide", evidence="helhetlig", db_path=dbp)
    feedback.record("A02_stilord_nb", "riktig", genre="slide", db_path=dbp)
    for _ in range(5):
        feedback.record("C05_oppsummeringsavslutning", "riktig_men_greit", genre="epost", db_path=dbp)
    feedback.record("B01_tankestrek", "riktig", db_path=dbp)

    rows = {(r["rule"], r["genre"]): r for r in feedback.summary(dbp)}
    a02 = rows[("A02_stilord_nb", "slide")]
    assert a02["total"] == 5 and a02["feil_andel"] == 0.8
    assert a02["advice"].startswith("stram")
    assert rows[("C05_oppsummeringsavslutning", "epost")]["advice"].startswith("gjør regelen til råd")
    assert rows[("B01_tankestrek", None)]["advice"].startswith("for få")
    assert feedback.summary(dbp, genre="epost")[0]["rule"] == "C05_oppsummeringsavslutning"
    assert "stram" in feedback.format_summary(feedback.summary(dbp))

    with sqlite3.connect(dbp) as c:
        assert c.execute("SELECT evidence FROM feedback WHERE evidence IS NOT NULL").fetchone()[0] == "helhetlig"


def test_migrates_old_table(tmp_path):
    dbp = tmp_path / "old.db"
    with sqlite3.connect(dbp) as c:
        c.execute("CREATE TABLE feedback (rule TEXT NOT NULL, verdict TEXT NOT NULL,"
                  " genre TEXT, comment TEXT, ts REAL NOT NULL)")
        c.execute("INSERT INTO feedback VALUES ('X', 'riktig', NULL, NULL, 0)")
    out = feedback.record("X", "feil", evidence="noe", db_path=dbp)
    assert out["total_feedback_for_rule"] == 2
    assert feedback.summary(dbp)[0]["total"] == 2
