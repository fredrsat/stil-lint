# Ordlistevalidering mot menneskelig baseline

Baseline: NoReC (ltgoslo/norec), bokmål, t.o.m. 2019, 42888 dokumenter, 17.3 mill. token. wordfreq nb-snapshot (før 2022).

Dette er den menneskelige halvdelen av frekvensratioen. Endelig
STRYK/BEHOLD krever LLM-siden (steg 5). Foreløpig tolkning:
- **hyppig** (> 10.0/mill. hos mennesker): dårlig tegn, kandidat for stryking
- **middels** (1.0-10.0/mill.): bare brukbar i tetthetsregel, ikke enkeltfunn
- **sjelden** (< 1.0/mill.): lovende tegn hvis LLM-siden viser overrepresentasjon

## A02_stilord_nb

| ord/frase | NoReC per mill. | wordfreq zipf | vurdering |
| --- | --- | --- | --- |
| understreker | 42.68 | 3.78 | hyppig - kandidat for stryking |
| vitner om | 25.56 | - | hyppig - kandidat for stryking |
| helhetlig | 21.80 | 3.75 | hyppig - kandidat for stryking |
| sømløst | 21.11 | 2.39 | hyppig - kandidat for stryking |
| banebrytende | 13.13 | 3.54 | hyppig - kandidat for stryking |
| skreddersydd | 12.72 | 3.54 | hyppig - kandidat for stryking |
| revolusjonerende | 10.99 | 3.39 | hyppig - kandidat for stryking |
| nøkkelen til | 8.27 | - | middels - kun tetthet |
| sentral rolle | 7.92 | - | middels - kun tetthet |
| belyser | 7.00 | 3.28 | middels - kun tetthet |
| sømløs | 6.88 | 2.06 | middels - kun tetthet |
| i en verden der | 6.53 | - | middels - kun tetthet |
| fremhever | 5.84 | 3.25 | middels - kun tetthet |
| i dagens samfunn | 1.68 | - | middels - kun tetthet |
| legger til rette for | 1.27 | - | middels - kun tetthet |
| spiller en viktig rolle | 0.93 | - | sjelden - lovende |
| paradigmeskifte | 0.87 | 2.79 | sjelden - lovende |
| synergi | 0.40 | 2.67 | sjelden - lovende |
| i stadig endring | 0.40 | - | sjelden - lovende |
| verdifull innsikt | 0.00 | - | sjelden - lovende |

## A03_skiltfraser

| ord/frase | NoReC per mill. | wordfreq zipf | vurdering |
| --- | --- | --- | --- |
| med andre ord | 131.04 | - | hyppig - kandidat for stryking |
| alt i alt | 52.22 | - | hyppig - kandidat for stryking |
| når det kommer til | 33.14 | - | hyppig - kandidat for stryking |
| til syvende og sist | 16.77 | - | hyppig - kandidat for stryking |
| kort sagt | 16.71 | - | hyppig - kandidat for stryking |
| det er verdt å nevne | 5.84 | - | middels - kun tetthet |
| det er viktig å merke seg | 0.40 | - | sjelden - lovende |
| la oss se nærmere på | 0.00 | - | sjelden - lovende |
| la oss dykke ned i | 0.00 | - | sjelden - lovende |
| la oss bryte det ned | 0.00 | - | sjelden - lovende |

## A05_forsterkere

| ord/frase | NoReC per mill. | wordfreq zipf | vurdering |
| --- | --- | --- | --- |
| faktisk | 442.74 | 5.64 | hyppig - kandidat for stryking |
| virkelig | 390.40 | 5.64 | hyppig - kandidat for stryking |
| utrolig | 113.58 | 5.36 | hyppig - kandidat for stryking |
| rett og slett | 196.97 | - | hyppig - kandidat for stryking |
| genuint | 23.42 | 3.26 | hyppig - kandidat for stryking |
| uten tvil | 20.82 | - | hyppig - kandidat for stryking |
| ærlig talt | 9.08 | - | middels - kun tetthet |
| helt ærlig | 4.11 | - | middels - kun tetthet |

## A08_oppblast

| ord/frase | NoReC per mill. | wordfreq zipf | vurdering |
| --- | --- | --- | --- |
| benytte | 15.38 | 4.56 | hyppig - kandidat for stryking |
| benytter | 33.14 | 4.52 | hyppig - kandidat for stryking |
| i forbindelse med | 19.60 | - | hyppig - kandidat for stryking |
| med hensyn til | 6.53 | - | middels - kun tetthet |
| implementere | 0.93 | 3.65 | middels - kun tetthet |
| anvende | 1.10 | 3.58 | middels - kun tetthet |
| anvender | 2.37 | 3.22 | middels - kun tetthet |
| optimalisere | 1.73 | 2.77 | middels - kun tetthet |
| implementerer | 0.23 | 2.80 | sjelden - lovende |
| optimaliserer | 0.46 | 1.62 | sjelden - lovende |
| fasilitere | 0.00 | 1.82 | sjelden - lovende |
| fasiliterer | 0.00 | 1.47 | sjelden - lovende |

## A10_metaforsubstantiv

| ord/frase | NoReC per mill. | wordfreq zipf | vurdering |
| --- | --- | --- | --- |
| reise | 115.08 | 5.10 | hyppig - kandidat for stryking |
| landskap | 56.15 | 4.13 | hyppig - kandidat for stryking |
| landskapet | 35.22 | 4.04 | hyppig - kandidat for stryking |
| reisen | 31.29 | 4.34 | hyppig - kandidat for stryking |
| fundamentet | 4.86 | 3.55 | middels - kun tetthet |
| kompass | 4.68 | 3.58 | middels - kun tetthet |
| økosystemet | 1.10 | 3.41 | middels - kun tetthet |
| økosystem | 1.85 | 3.16 | middels - kun tetthet |
| verktøykasse | 1.16 | 2.41 | middels - kun tetthet |
| verktøykassen | 0.58 | 2.03 | sjelden - lovende |
| byggesteiner | 0.52 | 2.23 | sjelden - lovende |
| byggestein | 0.29 | 2.20 | sjelden - lovende |

## D03_vag_kilde

| ord/frase | NoReC per mill. | wordfreq zipf | vurdering |
| --- | --- | --- | --- |
| mange opplever | 0.87 | - | sjelden - lovende |
| studier viser | 0.00 | - | sjelden - lovende |
| forskning viser | 0.00 | - | sjelden - lovende |
| eksperter mener | 0.00 | - | sjelden - lovende |
| det er bred enighet om | 0.00 | - | sjelden - lovende |

## E01_kalker

| ord/frase | NoReC per mill. | wordfreq zipf | vurdering |
| --- | --- | --- | --- |
| gjøre en forskjell | 0.93 | - | sjelden - lovende |
| på slutten av dagen | 0.35 | - | sjelden - lovende |
| tok et øyeblikk | 0.00 | - | sjelden - lovende |
| i person | 0.00 | - | sjelden - lovende |
| har du noen gang lurt på | 0.00 | - | sjelden - lovende |
| adressere problemet | 0.00 | - | sjelden - lovende |
| adressere et problem | 0.00 | - | sjelden - lovende |

## E06_preposisjonskalker

| ord/frase | NoReC per mill. | wordfreq zipf | vurdering |
| --- | --- | --- | --- |
| i form av | 73.91 | - | hyppig - kandidat for stryking |
| på daglig basis | 0.58 | - | sjelden - lovende |
| på en daglig basis | 0.00 | - | sjelden - lovende |

