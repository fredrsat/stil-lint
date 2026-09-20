# stil-lint

A style and quality linter for Norwegian (and English) text, delivered as an MCP
server and CLI. It judges whether a text reads like a human wrote it well — or
like unedited LLM output — using several independent layers, with TypeSafe's
Jev as the judgment layer.

stil-lint is a *style linter*, **not** an authorship detector. It reports
findings ("paragraph 2 has a not-X-but-Y contrast turn, p=0.88"), never "73%
AI-written". Detectors that try to decide authorship fail systematically and
punish non-native writers; the research behind this design choice is collected
in `ai-stil-lint-research.md` (in Norwegian).

The primary use case: automated agents (weather, transit, homework, groceries)
that send messages to a human should call this tool before sending, revise on
findings, and only then deliver. It also works as a personal style check for
prose.

## Quick start

```bash
git clone https://github.com/fredrsat/stil-lint
cd stil-lint
pip install -e ".[pptx]"

# Local check - nothing leaves your machine (layers 0-3)
stil-lint check text.md --genre sakprosa
echo "Oppdatering: Hei!" | stil-lint check --genre varsel --channel push

# With the Jev judgment layer (layer 4), directly against TypeSafe
export TYPESAFE_API_KEY=...
stil-lint check text.md --mode full

# Or through OpenRouter (same Decisions API, OpenRouter key)
export TYPESAFE_BASE_URL=https://openrouter.ai/api
export TYPESAFE_API_KEY=sk-or-...
export TYPESAFE_MODEL=jev-1.13        # OpenRouter uses short model IDs
stil-lint check text.md --mode full

stil-lint rules                        # list all rules
stil-lint bank-add --agent-id my-agent # remember a sent message (phrase bank)
stil-lint pptx deck.pptx               # check a PowerPoint deck (needs [pptx] extra)
stil-lint serve                        # start the MCP server (stdio)
```

MCP setup for Claude Code (stored in `~/.claude.json`):

```bash
# Directly against TypeSafe
claude mcp add stil-lint -e TYPESAFE_API_KEY=... -- stil-lint serve

# Through OpenRouter
claude mcp add stil-lint \
  -e TYPESAFE_API_KEY=sk-or-... \
  -e TYPESAFE_BASE_URL=https://openrouter.ai/api \
  -e TYPESAFE_MODEL=jev-1.13 \
  -- stil-lint serve
```

Omit the `-e` flags if you only need `mode: fast`. For Claude Desktop or other
clients, the equivalent JSON:

```json
{"mcpServers": {"stil-lint": {"command": "stil-lint", "args": ["serve"],
                              "env": {"TYPESAFE_API_KEY": "..."}}}}
```

## How an agent uses it

The intended loop is **check → revise → send → remember**. The agent drafts its
message, asks stil-lint for a verdict, fixes what the hints point at, sends,
and finally banks the sent text so tomorrow's near-duplicate gets caught.

### 1. Check the draft

The agent calls the `check_text` MCP tool before sending:

```json
{
  "text": "God morgen! ☀️ I dag blir det en nydelig dag! Gi meg beskjed hvis du vil vite mer!",
  "genre": "varsel",
  "channel": "push",
  "mode": "full",
  "agent_id": "weather-agent"
}
```

- `genre` picks the rule profile. A push alert has strict rules (max two
  sentences, no greeting); an essay does not.
- `channel` enables channel rules - markdown and emoji are flagged in `push`
  and `sms`, fine in `epost`.
- `mode: "full"` adds the Jev judgment layer (requires an API key).
  `mode: "fast"` runs only the local layers - nothing leaves the machine, so
  sensitive text (homework, family messages) can always be checked.
- `agent_id` enables the phrase-bank check against this agent's earlier
  messages.

### 2. Read the verdict

```json
{
  "verdict": "revise",
  "score": 0.0,
  "round": 1,
  "max_rounds": 2,
  "findings": [
    {"rule": "F02_hilsen_i_varsel", "severity": 3, "p": 1.0,
     "hint": "Hilsen eller signatur i et varsel. Stryk; varselet skal bare inneholde saken."},
    {"rule": "A04_chatbotrester", "severity": 3, "p": 1.0,
     "hint": "Chatbot-rest. Stryk hele frasen; mottakeren snakker ikke med en assistent."},
    {"rule": "C01_negativ_parallellisme", "severity": 2, "p": 0.78,
     "hint": "Si andre halvdel direkte og stryk første."}
  ],
  "positives": {"G01_konkret_detalj": 0.22},
  "missing": ["G01_konkret_detalj under 0.4 (p=0.22)"],
  "no_judgment": [],
  "meta": {"model": "jev-1.13", "ms": 692, "lang": "nb"}
}
```

Three possible verdicts:

- `pass` - send it.
- `revise` - fix what the hints say, call `check_text` again with `round: 2`.
- `pass_with_notes` - findings remain but the loop is over. After `max_rounds`
  (default 2) the verdict is always `pass_with_notes`, so an agent can never
  get stuck rewriting forever. This cap lives in the tool, not in the agent.

Note the `missing` field: the draft above has no concrete detail (G01). Empty,
generic text is *worse* than slightly AI-flavoured text with content - the
positive G-rules are the counterweight that stops an agent from optimizing
itself down to clean, empty prose.

### 3. Revise and re-check

The revised draft leads with the actionable fact, drops the greeting and the
chatbot tail, and adds the concrete details:

```
Klarvær i Oslo i morgen: sol fra morgenen av og opp mot 19 grader utover
dagen. Kjølig på skoleveien rundt 07, ta med jakke.
```

→ `{"verdict": "pass", "score": 1.0}`

### 4. After sending: remember it

```json
{"agent_id": "weather-agent", "text": "Klarvær i Oslo i morgen: ..."}
```

sent to the `bank_add` tool. If the agent sends a near-identical message
tomorrow, rule F05 fires ("same phrasing as an earlier message from this
agent") - measured as shingle overlap, and only hashes are stored, never the
text itself.

### System-prompt snippet for an agent

> Before sending any message to the user: call stil-lint's `check_text` with
> the draft, `genre: varsel`, `channel: push`, `mode: full`, and
> `agent_id: weather-agent`. If the verdict is `revise`, fix exactly what the
> hints say and check once more with `round: 2`. Send when you get `pass` or
> `pass_with_notes`. After sending, call `bank_add` with the text you sent.

## Checking presentations

`stil-lint pptx deck.pptx` extracts every slide (title + body) and the speaker
notes. Each slide is checked as one paragraph under the `slide` profile -
fragments, bullet lists and bold are the medium there, so those rules are off,
while generic content (D01), forced triads (C02), buzzwords (A02/A12) and
Title Case in Norwegian titles still count. Deck-level rules see the whole
presentation, so fractal repetition (C18: the same point on slides 2, 7 and
12) is caught. Speaker notes are prose and are checked with the prose profile.
Findings are reported per slide number. Hidden metadata slides (e.g.
AGENT-META) are skipped.

`hooks/pptx_stop_hook.py` is a Claude Code Stop hook that runs this check on
recently modified .pptx files and feeds the findings back to Claude once per
deck version - warn once, never nag. Register it in `~/.claude/settings.json`
under `hooks.Stop`. The hook runs locally (`mode: fast`) unless
`TYPESAFE_API_KEY` is present in its environment; putting the TypeSafe
variables in the `env` block of `~/.claude/settings.json` makes them available
to every Claude Code session, hooks included.

## MCP tools

| Tool | Purpose |
| --- | --- |
| `check_text` | Check a text; returns verdict, findings with hints, positives, missing |
| `list_rules` | Rules in effect, optionally filtered by genre profile |
| `explain_rule` | What a rule looks for, what it deliberately ignores (`not_for`), its hint |
| `record_feedback` | Mark a finding `riktig` (correct), `feil` (wrong) or `riktig_men_greit` (correct but fine) - calibration data |
| `bank_add` | Add a sent message to the agent's phrase bank |

`riktig_men_greit` matters: it is the data that lets severity be tuned per
genre over time.

## Architecture

```
text + genre + channel + language
  [0] preprocess.py  strip code/quotes/front matter, language guess, paragraph split
  [1] lex.py         regex and word lists (rules/lex.yaml)         local, ~5 ms
  [2] stat.py        rhythm, LIX, nominalization, connectors       local
  [3] bank.py        phrase bank per agent (SQLite, hashes only)   local
  [4] jev.py         Jev judgment, doc + paragraphs concurrently   api.typesafe.ai, ~0.7 s
  [5] gate.py        thresholds, no-judgment band 0.40-0.60,
                     genre profile, severity weights, verdict      policy in code
```

Design principles, distilled from the research document:

- **Report findings, not a verdict on authorship.** Single tells prove
  nothing; the gate weighs severity and genre, and that policy lives in code -
  the model is never asked whether a human should care.
- **A no-judgment band.** Jev answers around 0.5 on text it cannot read;
  probabilities in 0.40-0.60 are reported as "no judgment", never as weak
  findings. This matters extra for Norwegian.
- **Presence is not severity.** Contrast, judgment and clear claims are often
  the point of a text. Every finding carries a `keep_if` describing when to
  keep the flagged construction.
- **Positive checks.** A checklist only measures what is there; the G-rules
  (concrete detail, takes a position, key point first, still reads naturally)
  must clear a threshold for `pass`.
- **Privacy.** `mode: fast` is fully local. Jev responses are cached keyed on
  hash of (text, question, model); the text itself is never stored.

## Rules and profiles

- `rules/lex.yaml` - groups A (word choice), B (punctuation/formatting),
  C/D (regex-detectable structure and content), E (Norwegian-specific
  anglicisms), F (channel/agent rules). Word lists are corpus-validated where
  noted; unvalidated entries are marked as hypotheses.
- `rules/stat.yaml` - metadata for the statistical measures (sentence-length
  variance, nominalization density, connector openers, structure-vs-length,
  alert length, phrase-bank repetition).
- `rules/jev.yaml` - judgment rules sent to Jev, each with `what`, `not_for`,
  `criteria`, a fixed `hint` and `keep_if`. Written in Norwegian - measured
  better than English questions on Norwegian text (see below).
- `profiles/*.yaml` - `varsel` (push alerts), `melding` (informal messages),
  `epost`, `sakprosa` (essays/articles), `debatt` (op-eds: contrast rules off,
  taking a position required), `teknisk` (docs: list rules off). A profile
  disables rules, sets thresholds and severity weights, and lists required
  positives.

Rule hints are in Norwegian since the target text is Norwegian; an English
hint set would be a straightforward addition.

## Evaluation (bench/)

Everything is reproducible:

```bash
sh bench/fetch_corpus.sh                  # clone NoReC into bench/data/ (gitignored)
python bench/build_baseline.py            # n-gram baseline -> baseline_nb.json.gz
python bench/validate_wordlists.py        # word lists vs. human frequency
python bench/negative_control.py 500      # false-positive rate per rule, clean text
python bench/negative_control.py 60 full  # same, with the Jev layer
python bench/generate_pairs.py 100        # LLM continuations (Reinhart method)
python bench/generate_assistant.py        # LLM assistant-register texts
python bench/llm_ratio.py                 # overrepresentation vs. baseline
python bench/seeded_faults.py 10          # plant one known fault per rule, measure catch
```

Results as of 2026-09-20 (reports in `bench/`):

- **Human baseline**: NoReC, 42,888 Norwegian reviews 1998-2019 (17.3M tokens,
  pre-LLM), plus the `wordfreq` nb snapshot.
- **Negative control**: every rule under the 5% false-positive limit on clean
  human paragraphs (worst: uniform sentence rhythm at 3.4%). The first run
  caught a real bug - the Oxford-comma rule flagged 35% of human text because
  a comma before "og" between main clauses is correct Norwegian; rewritten to
  require an actual enumeration: 0%.
- **Word-list validation**: several hypothesized "AI phrases" turned out to be
  common human Norwegian ("med andre ord" 131/million) and were cut. Intensifier
  overuse (A05) was confirmed at 4-21x across all four model families. A new
  rule (A12) was added from discovered n-grams that are 15-113x
  overrepresented, with 0% false positives under a two-hit requirement.
- **Seeded faults**: regex layer catches 90-100%; Jev rules catch 70-100%
  after two questions were rewritten with sharper definitions (forced-triad
  went 0% → 100%, feeling-without-mechanism 10% → 80% at 5% FP).
- **Norwegian beats English question text** for Jev on Norwegian text
  (100% vs 60%, 70% vs 30% on two rules, and far fewer no-judgment answers), so
  the questions stay Norwegian.
- **Family-specific fingerprints** confirmed: each model family overuses its
  own phrases, so single-family word lists do not transfer.

Caveats: n is small (10 planted faults per rule, 60-500 control paragraphs);
read percentages against run-to-run variation. The LLM corpora are review
continuations and assistant answers from four families via OpenRouter
(gpt-5.4-mini, claude-sonnet-4.6, llama-4-maverick, gemini-3.8-flash).

## Work plan status

| Step (from the research document) | Status |
| --- | --- |
| 1 Verify Jev API and prior art | Done 2026-09-20 |
| 2 Repo setup | Done |
| 3 Layers 0-1, `mode: fast` without a key | Done |
| 4 Corpus and baseline frequencies | Done (NoReC + wordfreq nb) |
| 5 Paired Norwegian data, validate word lists | Done (800 continuations + 128 assistant texts, 4 families) |
| 6 Layer 2 (statistics) | Done (heuristic, spaCy optional) |
| 7 Layer 4 (Jev, cache, no-judgment band) | Done; verified live via OpenRouter |
| 8 Seeded-fault eval, nb vs en question text | Done; Norwegian questions win |
| 9 Gate, genre profiles, feedback | Done (weights are starting values) |
| 10 Phrase bank | Done |
| 11 Connect a real agent, two weeks of logging, pooled adjudication | Next |

Run the tests with `python -m pytest` (37 tests).

## License and data

Code: MIT. The NoReC corpus (used only for offline evaluation, never shipped)
is CC BY-NC 4.0; derived frequency lists are permitted for any use per the
corpus authors. Jev/TypeSafe and OpenRouter are paid APIs with their own terms.
