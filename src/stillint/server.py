"""MCP-server (FastMCP) med de fem verktøyene fra researchdokumentet del 7."""

from __future__ import annotations

try:  # mcp 2.x
    from mcp.server.mcpserver import MCPServer as FastMCP
except ModuleNotFoundError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP

from . import feedback as feedback_store
from .engine import Engine
from .rules import list_profiles

mcp = FastMCP("stil-lint")
_engine = Engine()


@mcp.tool()
async def check_text(
    text: str,
    genre: str = "sakprosa",
    channel: str | None = None,
    lang: str | None = None,
    mode: str = "fast",
    agent_id: str | None = None,
    round: int = 1,
    max_rounds: int = 2,
) -> dict:
    """Sjekk en tekst for AI-aktige stiltrekk og manglende kvaliteter.

    genre: en av profilene (varsel, melding, epost, sakprosa, debatt, teknisk).
    channel: push, sms, varsel, epost, chat - styrer kanalregler som markdown-forbud.
    mode: "fast" kjører bare lokale lag (ingenting sendes ut). "full" legger til
    Jev-skjønnslaget og krever TYPESAFE_API_KEY.
    agent_id: aktiverer frasebank-sjekken (F05) mot tidligere godkjente meldinger.
    round/max_rounds: omskrivingsrunde; etter max_rounds blir svaret alltid
    pass_with_notes slik at agenten ikke går i sløyfe.
    """
    return await _engine.check_text(
        text, genre=genre, channel=channel, lang=lang, mode=mode,
        agent_id=agent_id, round_num=round, max_rounds=max_rounds,
    )


@mcp.tool()
async def check_pptx(path: str, mode: str = "fast") -> dict:
    """Sjekk en PowerPoint-fil (.pptx) for AI-aktige stiltrekk.

    Hver slide sjekkes med slide-profilen (funn merkes med slidenummer),
    speaker notes sjekkes som prosa. path må være en absolutt sti serveren
    kan lese. mode: "fast" (lokalt) eller "full" (med Jev-skjønnslaget).
    """
    from pathlib import Path

    from .pptx_check import check_deck

    file = Path(path).expanduser()
    if not file.exists():
        return {"error": f"Finner ikke filen: {file}"}
    report = await check_deck(file, mode=mode, engine=_engine)
    return {"file": report.file, "verdict": report.verdict,
            "deck": report.deck_result, "notes": report.notes_result}


@mcp.tool()
def list_rules(genre: str | None = None) -> list[dict]:
    """List reglene i kraft, med lag, omfang og alvorlighet. Oppgi genre for å se profilfiltrert liste."""
    from .gate import active_rules
    from .rules import load_profile

    rules = _engine.config.rules
    if genre:
        rules = active_rules(_engine.config, load_profile(genre), genre)
    return [
        {"id": r.id, "layer": r.layer, "scope": r.scope, "lang": r.lang,
         "severity": r.severity, "positive": r.positive, "advisory": r.advisory}
        for r in rules
    ]


@mcp.tool()
def explain_rule(id: str) -> dict:
    """Forklar en regel: hva den ser etter, hva den ikke skal flagge, og hintet."""
    rule = _engine.config.by_id(id)
    if rule is None:
        return {"error": f"Ukjent regel: {id}", "kjente_profiler": list_profiles()}
    return {
        "id": rule.id, "layer": rule.layer, "scope": rule.scope,
        "severity": rule.severity, "what": rule.what, "not_for": rule.not_for,
        "pattern": rule.pattern, "words": rule.words or None,
        "hint": rule.hint, "keep_if": rule.keep_if,
    }


@mcp.tool()
def record_feedback(rule: str, verdict: str, genre: str | None = None, comment: str | None = None) -> dict:
    """Registrer om et funn var riktig, feil eller riktig_men_greit. Brukes til kalibrering."""
    return feedback_store.record(rule, verdict, genre=genre, comment=comment)


@mcp.tool()
def bank_add(agent_id: str, text: str) -> dict:
    """Legg en godkjent, sendt melding i frasebanken for agenten (grunnlag for F05)."""
    return _engine.bank_add(agent_id, text)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
