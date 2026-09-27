# DEEM som lokalt Jev-alternativ: pilotrapport (2026-09-27)

Testet [LibertAI DEEM](https://labs.libertai.io/papers/deem-open-machine-reflexes/)
(åpen /v1/systemone-implementasjon, Apache 2.0) som lokal erstatning for Jev,
på maskinen målgruppen faktisk har: M4 Pro, 24 GB.

## Oppsett

- Klienten trengte tre små endringer, nå i main: godta `"value"` i tillegg til
  `"noul"` i svar, konfigurerbar timeout (`TYPESAFE_TIMEOUT`), og seriell
  kallmodus (`STILLINT_JEV_SERIAL=1`) fordi DEEMs referanseserver henger seg
  ved samtidige forespørsler.
- Byttet backend er ellers bare miljøvariabler: `TYPESAFE_BASE_URL=http://localhost:8300`.

## deem-9b-v1: ukjørbar på 24 GB

bf16-vektene (17,9 GB) pluss transformers' referanseimplementasjon av Qwen3.5s
gated delta-attention allokerte over 30 GB på MPS -> OOM og svap-kollaps.
Røyk-testen som rakk å svare var lovende på norsk: plantet "ikke bare X, men Y"
-> p=0,97, "finnes konkret detalj" -> p=0,008 (begge riktige, skarpt kalibrert).
Men hvert kall tok ~30-60 s. Ikke videre testet.

Mulige veier for 9B lokalt: GGUF-kvantisering finnes
(mradermacher/deem-9b-v1-GGUF, ~5 GB i Q4) men krever egen letter-slot-adapter
rundt llama.cpp (~et dagsverk); eller vente på LibertAIs ARM/int8-runtime
(dagens Rust-kjerner er AVX-512/x86); eller en maskin med >= 32 GB.

## deem-0.8-v1: ubrukelig som dommer på norsk

Nøyaktig samme evaluering som Jev fikk (samme tekster, samme norske spørsmål,
cache-adskilt). Negativ kontroll = andel RENE menneskeavsnitt som flagges:

| regel | Jev FP | deem-0.8 FP | Jev fangst | deem-0.8 fangst |
| --- | --- | --- | --- | --- |
| C01 negativ parallellisme | 0 % | **98 %** | 100 % | 90 % |
| C02 tvunget tretall | 0 % | **43 %** | 100 % | 80 % |
| C04 oppsummerende slutt | 0 % | **22 %** | 100 % | 20 % |
| C06 halsrensk | 0 % | **20 %** | 100 % | 10 % |
| C10 påhengt tolkning | 0 % | **18 %** | 100 % | 70 % |
| D01 generisk | 0 % | **40 %** | - | - |
| D02 betydningsoppblåsing | 0 % | **8 %** | 80 % | 80 % |
| D05 følelse uten mekanisme | 5 % | 2 % | 80 % | 0 % |
| C18 fraktal gjentakelse | 0 % | **22 %** | - | - |

deem-0.8 sier i praksis "ja" til nesten alt på norsk: 98 % av ren menneskelig
tekst flagges for negativ parallellisme, og plantede tekster får 2-5 
tilleggsfunn i snitt. Fangsttallene er derfor verdiløse - en dommer som roper
ulv hele tiden "fanger" alt. Dette er nøyaktig svakhetsprofilen
researchdokumentet advarte mot hos billige dommere (Haiku: 37 av 54 rene
avsnitt flagget), og konsistent med papirets egne tall (0,333 på JevBench hard).

Norsk spørsmålstekst slo engelsk også på DEEM (C01 90/50, E01 90/20), så
funnet fra Jev-evalueringen står seg på tvers av modellfamilier.

## Konklusjon

- **deem-0.8: nei.** Kan ikke brukes til noe av dette.
- **deem-9b: kanskje, men ikke på denne maskinen i dag.** Kvalitetssignalet på
  norsk var reelt i røyk-testen, men uverifisert i skala. Revurder når (a) en
  ARM/int8-runtime finnes, (b) noen bygger GGUF-adapter, eller (c) maskinen
  har >= 32 GB.
- **Jev via OpenRouter forblir skjønnslaget.** For sensitive tekster er
  `mode: fast` fortsatt svaret; de lokale lagene er gode nok der (regex-laget
  fanget 100 % av sine plantede feil også i denne kjøringen).

Kostnad for piloten: ~20 GB disk (slettbart: `~/.cache/huggingface`,
`~/Code/deem`), noen timers kjøretid, 0 kr i API-kostnad.
