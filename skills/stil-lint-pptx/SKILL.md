---
name: stil-lint-pptx
description: Use whenever you create or edit a PowerPoint (.pptx) and the stil-lint MCP server is available. Runs the stil-lint style check on the deck via check_slides (works even when the file lives in a sandbox the server cannot read), and fixes what it flags before you call the deck finished.
---

# Style check for decks with stil-lint

stil-lint flags AI-sounding style in Norwegian text: generic bullets, buzzwords,
forced triads, Title Case in Norwegian titles, chatbot leftovers in notes.
Every .pptx you produce must pass it before you hand it over.

## Speaker notes: only when asked

Do not write speaker notes unless the user asked for them. The notes field is
not a place for everything that did not fit on the slide. If you think the
deck needs notes, ask first. When you check the deck, tell stil-lint whether
notes were requested (`notes_requested`); unrequested notes are flagged (F07).

## Which tool to call

- The stil-lint server runs on the user's machine. **If the .pptx was made in a
  sandbox** (`/home/claude`, `/mnt/user-data`, a cloud container), the server
  cannot open it, so **use `check_slides`** and send the text yourself.
- Only when the file is on the same machine as the server (Claude Code, local
  Cowork) may you call `check_pptx` with the absolute path. If `check_pptx`
  answers "Finner ikke filen", switch to `check_slides`.

## Steps

1. Extract the text per slide. Run the bundled script (needs `python-pptx`,
   `pip install python-pptx` if missing):

   ```bash
   python3 scripts/extract_slides.py deck.pptx > slides.json
   ```

   It prints a JSON list, one object per slide:
   `{"number": 1, "title": "...", "body": "...", "notes": "...", "hidden": false}`.
   Hidden slides (incl. AGENT-META) are included with `hidden: true`; the
   server skips them. Text inside tables and grouped shapes is included.

2. Call the `check_slides` tool with that list as `slides`, `mode: "fast"`
   (use `"full"` if the server has a Jev key configured) and
   `notes_requested: true/false` depending on whether the user asked for
   speaker notes. Pass the list as JSON, not as a string.

3. Read the verdict:
   - `pass`: done.
   - `revise`: for each finding, look at `slide`, `hint`, `sentence` and
     `keep_if`. Fix the slide text in the .pptx file itself (not just in your
     summary), unless the `keep_if` exception clearly applies. Then extract and
     check again. At most two rounds.
   - `pass_with_notes`: remaining findings are advisory. Mention them briefly.

4. Never work around a finding by deleting content. Empty, generic slides are
   worse than slightly AI-flavoured ones; the `missing` field (G01, concrete
   detail) tells you when a slide says nothing.

## Typical fixes

- Buzzwords (A02/A12): replace with the plain word, or cut the phrase.
- Forced triad (C02): keep the points that carry information, two or four is fine.
- Title Case in Norwegian (B07): only the first word and proper nouns capitalised.
- Generic bullet (D01): add the number, name, place or date that makes it specific.
- Chatbot leftovers in notes (A04): remove "Håper dette hjelper", "Gi beskjed hvis...".
- Unrequested notes (F07): delete the notes. Long notes (F08, advisory): cut to
  what will actually be said, or delete if they were never asked for.
