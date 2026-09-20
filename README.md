# stil-lint

Stil- og kvalitetslinter for norsk (og engelsk) tekst, levert som MCP-server og CLI.
Vurderer om en tekst holder menneskelig kvalitet eller er "AI-aktig", med flere
uavhengige lag der TypeSafes Jev er ett av dem.

Verktøyet er en stillinter, **ikke** en forfatterskapsdetektor. Det rapporterer
funn ("avsnitt 2 har en påhengt tolkning, p=0,88"), aldri "sannsynlighet for at
en LLM skrev dette". Begrunnelsen står i `ai-stil-lint-research.md`, del 1.

## Bruk

```bash
pip install -e .

# Lokal sjekk uten at noe forlater maskinen (lag 0-3)
stil-lint check tekst.md --genre sakprosa
echo "Oppdatering: Hei!" | stil-lint check --genre varsel --channel push

# Med Jev-skjønnslaget (lag 4), direkte mot TypeSafe
export TYPESAFE_API_KEY=...
stil-lint check tekst.md --mode full

# Eller via OpenRouter (samme Decisions API, OpenRouter-nøkkel)
export TYPESAFE_BASE_URL=https://openrouter.ai/api
export TYPESAFE_API_KEY=sk-or-...
export TYPESAFE_MODEL=jev-1.13        # OpenRouter bruker kortere modell-ID-er
stil-lint check tekst.md --mode full

stil-lint rules          # alle regler
stil-lint serve          # start MCP-serveren (stdio)
```

MCP-oppsett for Claude Code (legges i `~/.claude.json`):

```bash
# Direkte mot TypeSafe
claude mcp add stil-lint -e TYPESAFE_API_KEY=... -- stil-lint serve

# Via OpenRouter
claude mcp add stil-lint \
  -e TYPESAFE_API_KEY=sk-or-... \
  -e TYPESAFE_BASE_URL=https://openrouter.ai/api \
  -e TYPESAFE_MODEL=jev-1.13 \
  -- stil-lint serve
```

Utelat `-e`-flaggene hvis du bare skal bruke `mode: fast`.
For Claude Desktop eller andre klienter, tilsvarende i JSON:

```json
{"mcpServers": {"stil-lint": {"command": "stil-lint", "args": ["serve"],
                              "env": {"TYPESAFE_API_KEY": "..."}}}}
```

Verktøy: `check_text`, `list_rules`, `explain_rule`, `record_feedback`, `bank_add`.
Svar-skjemaet (verdict/score/findings/positives/missing/no_judgment) er beskrevet
i researchdokumentet del 7.

## Arkitektur

```
tekst + sjanger + kanal + språk
  [0] preprocess.py  fjern kode/sitater/front matter, språkgjetting, avsnittsdeling
  [1] lex.py         regex og ordlister (rules/lex.yaml)          lokalt
  [2] stat.py        rytme, LIX, nominalisering, koblingsord      lokalt
  [3] bank.py        frasebank per agent (SQLite, bare hasher)    lokalt
  [4] jev.py         Jev-skjønn, dok + avsnitt samtidig, cache    api.typesafe.ai
  [5] gate.py        terskler, ingen-vurdering-bånd 0,40-0,60,
                     sjangerprofil, alvorlighetsvekt, verdict     policy i kode
```

- `mode: fast` kjører lag 0-3 og er fullverdig for sensitive tekster.
- Jev-svar caches på hash av (tekst, spørsmål, modell); tekst lagres aldri.
- Etter `max_rounds` omskrivingsrunder returneres alltid `pass_with_notes`
  slik at en agent ikke går i sløyfe.
- Positive signaler (G-reglene) kreves for `pass` per profil - motvekten mot
  at en agent optimaliserer seg til ren, tom tekst.

## Regler og profiler

- `rules/lex.yaml` - gruppe A, B, E, F (regex/ordlister). **De norske ordlistene
  er hypoteser** og skal valideres med frekvensratio mot korpus (del 8) før
  terskler strammes.
- `rules/stat.yaml` - metadata for de statistiske målene (C08, C11, A11, B05, F01, F05).
- `rules/jev.yaml` - de ti prioriterte skjønnsreglene pluss G-gruppen, med
  `what`/`not_for`/`criteria`/`hint`/`keep_if` etter mønster fra snifftest og
  slopcheck-jev.
- `profiles/*.yaml` - varsel, melding, epost, sakprosa, debatt, teknisk. En
  profil slår regler av, setter terskler og krever positive signaler.

## Status mot arbeidsrekkefølgen (research-doc del 9)

| Steg | Status |
| --- | --- |
| 1 Verifiser Jev-API og prior art | Gjort 2026-09-20 (docs.typesafe.ai, snifftest, slopcheck-jev) |
| 2 Repo-oppsett | Gjort |
| 3 Lag 0-1, `mode: fast` uten nøkkel | Gjort |
| 4 Korpus og baseline-frekvenser | Gjort: NoReC (42 888 dok, 17,3 mill. token) + wordfreq nb. Se `bench/` |
| 5 Parvise norske data, valider A02/E01 | Gjort: 800 fortsettelser + 128 assistentsvar fra 4 modellfamilier (`bench/report_llm_ratio.md`, `bench/report_assistant.md`). A05 bekreftet, A12 lagt til, A04 utvidet med plassholder-mønster. Presenslistene forblir presisjonsregler (for sjeldne til å måles på 26k token, 0 FP-kostnad) |
| 6 Lag 2 (stat) | Gjort (heuristisk, uten spaCy; terskler er startverdier) |
| 7 Lag 4 (Jev, ti regler, cache, bånd) | Gjort; verifisert live via OpenRouter |
| 8 Seeded-fault-eval, norsk vs engelsk spørsmålstekst | Gjort (`bench/report_seeded_faults.md`): regex-laget 90-100 %, Jev-reglene 70-100 % etter spørsmålsomskriving (C02: 0->100 %, D05: 10->80 %). Norsk spørsmålstekst slår engelsk (C04: 100 mot 60 %, E01: 70 mot 30 %) - norsk beholdes. Jev-negativ kontroll: D05 5 % etter not_for-fiks + terskel 0,8 |
| 9 Gate, profiler, `record_feedback` | Gjort (vekter er startverdier) |
| 10 Frasebank | Gjort |
| 11 Koble på bussvarsel-agenten, to ukers logging | Ikke påbegynt |

## Korpus og evaluering (`bench/`)

```bash
sh bench/fetch_corpus.sh                 # kloner NoReC til bench/data/ (gitignorert)
python bench/build_baseline.py           # n-gram-baseline -> bench/data/baseline_nb.json.gz
python bench/validate_wordlists.py       # ordlister mot menneskelig frekvens
python bench/negative_control.py 500     # falsk-positiv-rate per regel på ren tekst
```

Resultater per 2026-09-20 (`bench/report_wordlists.md`, `bench/report_negative_control.md`):

- Flere fraser fra hypoteselistene viste seg vanlige i menneskelig norsk og er
  strøket fra tilstedeværelsesreglene ("med andre ord" 131/mill., "alt i alt"
  52/mill., "i form av" 74/mill.). Endelig dom krever LLM-siden av ratioen (steg 5).
- B08 (Oxford-komma) flagget 35 % av rene avsnitt før omskriving (komma foran
  "og" mellom helsetninger er korrekt norsk); etter krav om ekte oppramsing: 0 %.
- Alle regler ligger nå under 5 %-grensen i negativ kontroll (verst: C08 på 3,4 %).
- 473 uflaggede NoReC-avsnitt ligger i `bench/data/clean_paragraphs.jsonl` som
  grunnlag for seeded-fault-evalueringen.

LLM-siden (`bench/generate_pairs.py` + `bench/llm_ratio.py`, `bench/report_llm_ratio.md`):

- 800 norske fortsettelser (Reinhart-metoden) fra gpt-5.4-mini, claude-sonnet-4.6,
  llama-4-maverick og gemini-3.8-flash, nøytral og "skriv menneskelig"-variant.
- A05 (forsterkere) bekreftet 4-21x overrepresentert på tvers av alle fire familier.
- Ny regel A12: n-gram 15-113x overrepresentert ("føles både", "det høres kanskje",
  "resultatet er en" ...), 0 % falske positiver på menneskelig tekst med to-treffs-krav.
- Fingeravtrykkene er familiespesifikke, som Antislop-artikkelen fant.
- Viktig forbehold: fortsettelses-oppsettet undertrykker assistent-registeret, så
  presenslistene (A02, A08) er verken bekreftet eller avkreftet av denne runden.
  Neste validering bør bruke assistent-oppgaver (svar, meldinger) i stedet.

Kjør testene med `python -m pytest` (35 tester).
