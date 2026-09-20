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

# Med Jev-skjønnslaget (lag 4)
export TYPESAFE_API_KEY=...
stil-lint check tekst.md --mode full

stil-lint rules          # alle regler
stil-lint serve          # start MCP-serveren (stdio)
```

MCP-oppsett (f.eks. i `claude_desktop_config.json` eller `.mcp.json`):

```json
{"mcpServers": {"stil-lint": {"command": "stil-lint", "args": ["serve"]}}}
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
| 4 Korpus og baseline-frekvenser | Ikke påbegynt |
| 5 Parvise norske data, valider A02/E01 | Ikke påbegynt |
| 6 Lag 2 (stat) | Gjort (heuristisk, uten spaCy; terskler er startverdier) |
| 7 Lag 4 (Jev, ti regler, cache, bånd) | Kode gjort; ikke kjørt mot API (krever nøkkel) |
| 8 Seeded-fault-eval, norsk vs engelsk spørsmålstekst | Ikke påbegynt |
| 9 Gate, profiler, `record_feedback` | Gjort (vekter er startverdier) |
| 10 Frasebank | Gjort |
| 11 Koble på bussvarsel-agenten, to ukers logging | Ikke påbegynt |

Kjør testene med `python -m pytest` (33 tester).
