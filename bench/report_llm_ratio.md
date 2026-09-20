# LLM-siden av frekvensratioen

Materiale: 800 fortsettelser fra 4 modeller (33k token). Baseline: NoReC (ltgoslo/norec), bokmål, t.o.m. 2019 (17.3 mill. token).

**Viktig forbehold om register:** materialet er *fortsettelser av anmeldelser* (Reinhart-metoden). Modellene hermer sjangeren, så assistent-registerets stilord (banebrytende, i dagens samfunn, chatbot-fraser) forekommer naturlig nok ikke. STRYK i tabellen under betyr derfor "ikke overrepresentert i denne sjangeren", ikke at ordet er friskmeldt i agent- og assistenttekst. Presenslistene (A02, A08 m.fl.) må valideres separat med assistent-oppgaver (svar på spørsmål, skriv en melding) før de strykes. BEHOLD-dommer og nye kandidater er derimot gyldige: de er overrepresentert til tross for at modellene prøver å treffe menneskelig sjanger.

## Ordlistevalidering: endelig ratio

Behold: ratio >= 3.0 og >= 5 LLM-forekomster. Stryk: ratio < 2.0. Ellers: usikker (trenger mer data).

| regel | ord/frase | LLM/mill. | menneske/mill. | ratio | dom |
| --- | --- | --- | --- | --- | --- |
| A02_stilord_nb | banebrytende | 0.0 | 13.13 | 0.0x | STRYK |
| A02_stilord_nb | revolusjonerende | 0.0 | 10.99 | 0.0x | STRYK |
| A02_stilord_nb | sømløs | 29.9 | 6.88 | 4.3x | usikker |
| A02_stilord_nb | sømløst | 119.7 | 21.11 | 5.6x | usikker |
| A02_stilord_nb | helhetlig | 29.9 | 21.80 | 1.4x | STRYK |
| A02_stilord_nb | skreddersydd | 0.0 | 12.72 | 0.0x | STRYK |
| A02_stilord_nb | sentral rolle | 0.0 | 7.92 | 0.0x | STRYK |
| A02_stilord_nb | spiller en viktig rolle | 0.0 | 0.93 | 0.1x | STRYK |
| A02_stilord_nb | vitner om | 29.9 | 25.56 | 1.2x | STRYK |
| A02_stilord_nb | understreker | 0.0 | 42.68 | 0.0x | STRYK |
| A02_stilord_nb | belyser | 0.0 | 7.00 | 0.0x | STRYK |
| A02_stilord_nb | fremhever | 0.0 | 5.84 | 0.0x | STRYK |
| A02_stilord_nb | legger til rette for | 0.0 | 1.27 | 0.1x | STRYK |
| A02_stilord_nb | i stadig endring | 0.0 | 0.40 | 0.2x | STRYK |
| A02_stilord_nb | i dagens samfunn | 0.0 | 1.68 | 0.1x | STRYK |
| A02_stilord_nb | i en verden der | 29.9 | 6.53 | 4.5x | usikker |
| A02_stilord_nb | verdifull innsikt | 0.0 | 0.00 | 1.0x | STRYK |
| A02_stilord_nb | nøkkelen til | 0.0 | 8.27 | 0.0x | STRYK |
| A02_stilord_nb | synergi | 0.0 | 0.40 | 0.2x | STRYK |
| A02_stilord_nb | paradigmeskifte | 0.0 | 0.87 | 0.1x | STRYK |
| A03_skiltfraser | det er viktig å merke seg | 0.0 | 0.40 | 0.2x | STRYK |
| A03_skiltfraser | det er verdt å nevne | 0.0 | 5.84 | 0.0x | STRYK |
| A03_skiltfraser | la oss se nærmere på | 0.0 | 0.00 | 1.0x | STRYK |
| A03_skiltfraser | la oss dykke ned i | 0.0 | 0.00 | 1.0x | STRYK |
| A03_skiltfraser | la oss bryte det ned | 0.0 | 0.00 | 1.0x | STRYK |
| A05_forsterkere | ærlig talt | 119.7 | 9.08 | 13.1x | usikker |
| A05_forsterkere | helt ærlig | 89.8 | 4.11 | 21.4x | usikker |
| A05_forsterkere | virkelig | 1825.7 | 390.40 | 4.7x | **BEHOLD** |
| A05_forsterkere | faktisk | 1855.7 | 442.74 | 4.2x | **BEHOLD** |
| A05_forsterkere | utrolig | 478.9 | 113.58 | 4.2x | **BEHOLD** |
| A05_forsterkere | genuint | 149.7 | 23.42 | 6.4x | **BEHOLD** |
| A05_forsterkere | rett og slett | 808.1 | 196.97 | 4.1x | **BEHOLD** |
| A08_oppblast | benytte | 0.0 | 15.38 | 0.0x | STRYK |
| A08_oppblast | benytter | 0.0 | 33.14 | 0.0x | STRYK |
| A08_oppblast | anvende | 0.0 | 1.10 | 0.1x | STRYK |
| A08_oppblast | anvender | 0.0 | 2.37 | 0.0x | STRYK |
| A08_oppblast | implementere | 0.0 | 0.93 | 0.1x | STRYK |
| A08_oppblast | implementerer | 0.0 | 0.23 | 0.3x | STRYK |
| A08_oppblast | fasilitere | 0.0 | 0.00 | 1.0x | STRYK |
| A08_oppblast | fasiliterer | 0.0 | 0.00 | 1.0x | STRYK |
| A08_oppblast | optimalisere | 0.0 | 1.73 | 0.1x | STRYK |
| A08_oppblast | optimaliserer | 0.0 | 0.46 | 0.2x | STRYK |
| A08_oppblast | i forbindelse med | 0.0 | 19.60 | 0.0x | STRYK |
| A08_oppblast | med hensyn til | 0.0 | 6.53 | 0.0x | STRYK |
| A10_metaforsubstantiv | reise | 149.7 | 115.08 | 1.3x | STRYK |
| A10_metaforsubstantiv | reisen | 89.8 | 31.29 | 2.9x | usikker |
| A10_metaforsubstantiv | landskap | 89.8 | 56.15 | 1.6x | STRYK |
| A10_metaforsubstantiv | landskapet | 59.9 | 35.22 | 1.7x | STRYK |
| A10_metaforsubstantiv | økosystem | 0.0 | 1.85 | 0.1x | STRYK |
| A10_metaforsubstantiv | økosystemet | 0.0 | 1.10 | 0.1x | STRYK |
| A10_metaforsubstantiv | verktøykasse | 0.0 | 1.16 | 0.1x | STRYK |
| A10_metaforsubstantiv | verktøykassen | 0.0 | 0.58 | 0.1x | STRYK |
| A10_metaforsubstantiv | byggestein | 0.0 | 0.29 | 0.3x | STRYK |
| A10_metaforsubstantiv | byggesteiner | 0.0 | 0.52 | 0.2x | STRYK |
| A10_metaforsubstantiv | fundamentet | 0.0 | 4.86 | 0.0x | STRYK |
| A10_metaforsubstantiv | kompass | 0.0 | 4.68 | 0.0x | STRYK |
| D03_vag_kilde | studier viser | 0.0 | 0.00 | 1.0x | STRYK |
| D03_vag_kilde | forskning viser | 0.0 | 0.00 | 1.0x | STRYK |
| D03_vag_kilde | eksperter mener | 0.0 | 0.00 | 1.0x | STRYK |
| D03_vag_kilde | mange opplever | 0.0 | 0.87 | 0.1x | STRYK |
| D03_vag_kilde | det er bred enighet om | 0.0 | 0.00 | 1.0x | STRYK |
| E01_kalker | tok et øyeblikk | 0.0 | 0.00 | 1.0x | STRYK |
| E01_kalker | i person | 0.0 | 0.00 | 1.0x | STRYK |
| E01_kalker | gjøre en forskjell | 0.0 | 0.93 | 0.1x | STRYK |
| E01_kalker | på slutten av dagen | 0.0 | 0.35 | 0.2x | STRYK |
| E01_kalker | adressere et problem | 0.0 | 0.00 | 1.0x | STRYK |
| E01_kalker | adressere problemet | 0.0 | 0.00 | 1.0x | STRYK |
| E01_kalker | har du noen gang lurt på | 0.0 | 0.00 | 1.0x | STRYK |
| E06_preposisjonskalker | på en daglig basis | 0.0 | 0.00 | 1.0x | STRYK |
| E06_preposisjonskalker | på daglig basis | 0.0 | 0.58 | 0.1x | STRYK |

## Nye kandidater: mest overrepresenterte n-gram (samlet)

### Unigram

| n-gram | LLM-antall | LLM/mill. | menneske/mill. | ratio |
| --- | --- | --- | --- | --- |
| presisjon | 18 | 538.7 | 22.55 | 24x |
| ho | 22 | 658.5 | 47.48 | 14x |
| energi | 30 | 897.9 | 77.32 | 12x |
| resultatet | 59 | 1765.9 | 157.01 | 11x |
| overraskende | 72 | 2155.0 | 195.40 | 11x |
| stemningen | 31 | 927.8 | 90.62 | 10x |
| rå | 23 | 688.4 | 67.54 | 10x |
| funker | 23 | 688.4 | 71.71 | 10x |
| treffer | 37 | 1107.4 | 120.86 | 9x |
| tonen | 15 | 449.0 | 50.14 | 9x |
| usedvanlig | 19 | 568.7 | 65.29 | 9x |
| plata | 19 | 568.7 | 65.46 | 9x |
| føles | 89 | 2663.8 | 319.04 | 8x |
| varme | 34 | 1017.6 | 122.65 | 8x |
| sjarmerende | 33 | 987.7 | 123.12 | 8x |
| tydelig | 58 | 1736.0 | 217.32 | 8x |
| skikkelig | 40 | 1197.2 | 150.93 | 8x |
| ærlig | 15 | 449.0 | 58.00 | 8x |
| sjarm | 15 | 449.0 | 58.87 | 8x |
| liksom | 15 | 449.0 | 75.47 | 6x |
| umiddelbart | 16 | 478.9 | 81.83 | 6x |
| nettopp | 43 | 1287.0 | 223.97 | 6x |
| plutselig | 27 | 808.1 | 142.43 | 6x |
| synd | 15 | 449.0 | 82.46 | 5x |
| umulig | 19 | 568.7 | 107.62 | 5x |

### Bigram

| n-gram | LLM-antall | LLM/mill. | menneske/mill. | ratio |
| --- | --- | --- | --- | --- |
| føles både | 10 | 299.3 | 2.54 | 113x |
| energi som | 12 | 359.2 | 5.84 | 60x |
| overraskende godt | 10 | 299.3 | 5.84 | 50x |
| presisjon og | 10 | 299.3 | 6.07 | 49x |
| høres kanskje | 15 | 449.0 | 9.54 | 47x |
| overraskende bra | 13 | 389.1 | 9.19 | 42x |
| et usedvanlig | 10 | 299.3 | 7.29 | 41x |
| personlig og | 10 | 299.3 | 7.98 | 37x |
| faktisk ganske | 11 | 329.2 | 10.00 | 33x |
| rå og | 10 | 299.3 | 9.89 | 30x |
| denne nye | 11 | 329.2 | 13.01 | 25x |
| det nettopp | 10 | 299.3 | 13.82 | 22x |
| det funker | 15 | 449.0 | 21.57 | 21x |
| aldri helt | 15 | 449.0 | 22.73 | 20x |
| varme og | 16 | 478.9 | 24.35 | 20x |
| synd for | 11 | 329.2 | 16.71 | 20x |
| og resultatet | 12 | 359.2 | 18.68 | 19x |
| i magen | 10 | 299.3 | 16.54 | 18x |
| er nettopp | 20 | 598.6 | 33.31 | 18x |
| tør å | 11 | 329.2 | 18.91 | 17x |
| tydelig at | 25 | 748.3 | 43.95 | 17x |
| resultatet er | 42 | 1257.1 | 79.46 | 16x |
| det høres | 22 | 658.5 | 41.64 | 16x |
| som føles | 11 | 329.2 | 21.34 | 15x |
| samme tid | 19 | 568.7 | 37.18 | 15x |

### Trigram

| n-gram | LLM-antall | LLM/mill. | menneske/mill. | ratio |
| --- | --- | --- | --- | --- |
| det høres kanskje | 13 | 389.1 | 4.97 | 77x |
| og det funker | 8 | 239.4 | 3.93 | 59x |
| resultatet er en | 24 | 718.3 | 19.66 | 36x |
| er en plate | 8 | 239.4 | 6.71 | 35x |
| som er både | 13 | 389.1 | 11.05 | 35x |
| det er nettopp | 20 | 598.6 | 19.55 | 30x |
| er det nettopp | 9 | 269.4 | 10.64 | 25x |
| er tydelig at | 15 | 449.0 | 18.68 | 24x |
| en plate som | 13 | 389.1 | 16.77 | 23x |
| det er tydelig | 15 | 449.0 | 20.41 | 22x |
| seg igjen i | 9 | 269.4 | 13.99 | 19x |
| vanskelig å ikke | 8 | 239.4 | 13.24 | 18x |
| på samme tid | 17 | 508.8 | 28.74 | 18x |
| en måte som | 18 | 538.7 | 32.79 | 16x |
| det er nesten | 16 | 478.9 | 31.23 | 15x |
| likevel er det | 17 | 508.8 | 34.58 | 15x |
| det gjør at | 12 | 359.2 | 24.81 | 14x |
| gjør at man | 10 | 299.3 | 20.93 | 14x |
| samtidig er det | 13 | 389.1 | 31.34 | 12x |
| på en måte | 20 | 598.6 | 57.31 | 10x |
| det er noe | 26 | 778.2 | 75.12 | 10x |
| og det gjør | 9 | 269.4 | 27.53 | 10x |
| det er kanskje | 10 | 299.3 | 42.45 | 7x |
| det er jo | 10 | 299.3 | 45.45 | 7x |
| som gjør at | 25 | 748.3 | 118.49 | 6x |

## Familiespesifikke fingeravtrykk (topp bigram per modell)

- **anthropic/claude-sonnet-4.6** (9k token): er liksom (80x), nesten litt (46x), kjenne seg (32x), det funker (31x), og resultatet (30x), aldri helt (30x), seg igjen (28x), som føles (26x)
- **google/gemini-3.8-flash** (8k token): første sekund (121x), høres kanskje (103x), denne nye (57x), i magen (52x), kanskje litt (32x), jeg må (30x), innrømme at (27x), litt vel (24x)
- **meta-llama/llama-4-maverick** (8k token): et usedvanlig (124x), personlig og (98x), jeg gleder (88x), gleder meg (66x), rå og (66x), faktisk ganske (65x), havner på (55x), forfatteren har (54x)
- **openai/gpt-5.4-mini** (9k token): føles både (296x), gjør historien (207x), samtidig blir (148x), nettopp i (126x), overraskende godt (113x), energi som (94x), det nettopp (80x), med varme (77x)

## Parvis separasjon, mode=fast (uten Jev)

Samme åpning; menneskets fortsettelse mot modellens. Funn per tekst og
andel tekster med minst ett funn.

| modell (variant) | n | funn/tekst menneske | funn/tekst LLM | flagget menneske | flagget LLM |
| --- | --- | --- | --- | --- | --- |
| anthropic/claude-sonnet-4.6 (menneskelig) | 100 | 0.00 | 0.12 | 0% | 10% |
| anthropic/claude-sonnet-4.6 (noytral) | 100 | 0.00 | 0.11 | 0% | 10% |
| google/gemini-3.8-flash (menneskelig) | 100 | 0.00 | 0.14 | 0% | 13% |
| google/gemini-3.8-flash (noytral) | 100 | 0.00 | 0.06 | 0% | 6% |
| meta-llama/llama-4-maverick (menneskelig) | 100 | 0.00 | 0.09 | 0% | 9% |
| meta-llama/llama-4-maverick (noytral) | 100 | 0.00 | 0.04 | 0% | 3% |
| openai/gpt-5.4-mini (menneskelig) | 100 | 0.00 | 0.14 | 0% | 14% |
| openai/gpt-5.4-mini (noytral) | 100 | 0.00 | 0.13 | 0% | 13% |

Merk: mode=fast måler bare regex/stat-lagene. Jev-laget (skjønn) er der
hovedskillet ventes; det måles i seeded-fault-evalueringen (steg 8).
