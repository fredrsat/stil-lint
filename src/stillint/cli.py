"""Kommandolinje for lokal bruk og evaluering: `stil-lint check fil.md --genre varsel`."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .engine import Engine


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="stil-lint", description="Stil- og kvalitetslinter for norsk tekst")
    sub = parser.add_subparsers(dest="cmd", required=True)

    check = sub.add_parser("check", help="Sjekk en fil eller stdin")
    check.add_argument("file", nargs="?", help="Fil (utelat for stdin)")
    check.add_argument("--genre", default="sakprosa")
    check.add_argument("--channel", default=None)
    check.add_argument("--lang", default=None)
    check.add_argument("--mode", choices=["fast", "full"], default="fast")
    check.add_argument("--agent-id", default=None)
    check.add_argument("--json", action="store_true", help="Rått JSON-svar")

    sub.add_parser("rules", help="List alle regler")
    sub.add_parser("serve", help="Start MCP-serveren")

    args = parser.parse_args(argv)
    engine = Engine()

    if args.cmd == "rules":
        for r in engine.config.rules:
            flags = "+" if r.positive else ("råd" if r.advisory else str(r.severity))
            print(f"{r.id:35s} {r.layer:6s} {r.scope:9s} sev={flags}")
        return 0

    if args.cmd == "serve":
        from .server import main as serve_main
        serve_main()
        return 0

    text = Path(args.file).read_text() if args.file else sys.stdin.read()
    result = asyncio.run(engine.check_text(
        text, genre=args.genre, channel=args.channel, lang=args.lang,
        mode=args.mode, agent_id=args.agent_id,
    ))

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        m = result["meta"]
        print(f"{result['verdict'].upper()}  score={result['score']}  "
              f"lang={m['lang']} genre={m['genre']} mode={m['mode']} {m['ms']}ms")
        for f in result["findings"]:
            where = f"avsnitt {f['paragraph']}" if f.get("paragraph") is not None else "dokument"
            note = " (råd)" if f.get("advisory") else ""
            print(f"  [{f['rule']}] {where}, p={f['p']}, sev={f['severity']}{note}")
            print(f"      {f['hint']}")
            if f.get("evidence"):
                print(f"      treff: {f['evidence']}")
        for m_ in result["missing"]:
            print(f"  MANGLER: {m_}")
        if result["no_judgment"]:
            print(f"  Ingen vurdering (0,40-0,60): {', '.join(result['no_judgment'])}")
        if result["meta"].get("jev_error"):
            print(f"  Jev-feil: {result['meta']['jev_error']}")
    return 0 if result["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
