# AI-stil-lint: researchgrunnlag og byggeplan

Overleveringsdokument til arbeid i CLI. Dato: 2026-09-20.

Mål: en MCP-server som vurderer om en tekst holder menneskelig kvalitet eller er "AI-aktig", med flere uavhengige lag der TypeSafes Jev er ett av dem. Verktøyet skal brukes av agenter (vær, buss, lekser, matbestilling) før de sender noe til et menneske, og som personlig stilsjekk.

Verktøyet er en stil- og kvalitetslinter. Det er ikke en forfatterskapsdetektor, og skal aldri rapportere "sannsynlighet for at en LLM skrev dette". Begrunnelsen står i del 1.

Innhold:

1. Hva forskningen sier, og hva den ikke sier
2. Katalog over kjennetegn (grunnlag for regler og Jev-spørsmål)
3. Hvordan skrive spørsmål til Jev
4. Referansekorpus fra før 2022
5. Andre verktøy og tilnærminger
6. Prior art med Jev på GitHub, og hva som er verdt å låne
7. Foreslått arkitektur for MCP-serveren
8. Evalueringsplan
9. Arbeidsrekkefølge
10. Kilder

---

## 1. Hva forskningen sier, og hva den ikke sier

### Kjennetegnene er reelle på korpusnivå

- Reinhart m.fl. (PNAS 2025) sammenlignet menneskeskrevne tekster med LLM-fortsettelser av de samme tekstene. Instruksjonstunede modeller bruker presens partisipp-ledd omtrent 5 ganger så ofte som mennesker og nominaliseringer omtrent 2 ganger så ofte. Enkelte ord (tapestry, camaraderie) forekommer over 100 ganger så ofte. Funnene gjelder grammatikk og retorikk, ikke bare ordvalg, og de er sterkere i instruksjonstunede modeller enn i basemodeller.
- Kobak m.fl. (Science Advances 2025) fant at minst 13,5 % av PubMed-abstracts i 2024 bar preg av LLM-bearbeiding, målt som overskuddsfrekvens av stilord. "Delves" lå 28 ganger over forventet.
- Paech m.fl. (Antislop, ICLR 2026) måler overrepresentasjon av ord, bigram og trigram mot en menneskelig baseline (wordfreq pluss Reddit/Gutenberg). Hver modellfamilie har sitt eget "slop-fingeravtrykk", og fingeravtrykkene klynger seg etter familie. Konsekvens: en ordliste bygd på GPT-4-tekst treffer dårlig på Llama- eller Claude-tekst.
- Wikipedias "Signs of AI writing" (WikiProject AI Cleanup) er den mest gjennomarbeidede feltguiden. En av vedlikeholderne oppgir at regnearket hennes har 106 tegn sortert etter styrke, mange av dem varianter av hverandre.
- Russell m.fl. (preprint 2025) viste at folk som selv bruker LLM-er mye, gjenkjenner AI-tekst riktig i rundt 90 % av tilfellene. Folk uten slik erfaring treffer knapt bedre enn tilfeldig. Mønstrene er altså lærbare, og det er et argument for at en modell også kan lære dem.

### Kjennetegnene er svake på dokumentnivå

- Ingen enkelttegn beviser noe. Wikipedia-guiden sier dette selv.
- Tankestreken er en finjusteringsartefakt, ikke en AI-egenskap. En preprint (Freeburg 2026, ikke fagfellevurdert) målte GPT-4.1 til ca. 10,6 per 1000 ord, GPT-5.4 til 1,4 og Llama-modellene til 0. Mark Twain ligger på ca. 10. Regler på tegnsetting må derfor være terskler per sjanger, ikke forbud.
- "AI-ordene" begynte å stige i PubMed allerede i 2020 (Matsui 2025). Ordfrekvens sier noe om et korpus og nesten ingenting om én tekst.
- Detektorer som forsøker å avgjøre forfatterskap, feiler systematisk. Liang m.fl. (Patterns 2023): syv detektorer flagget i snitt 61 % av TOEFL-essays skrevet av andrespråksbrukere. Weber-Wulff m.fl. (2023): 14 detektorer lå alle under 80 % treffsikkerhet og falt til 26 % på maskinparafrasert tekst.
- Menneskers språk påvirkes av LLM-er. Grensen flytter seg, og tekster etter 2022 er ikke lenger en ren menneskelig baseline.

### Hva dette betyr for designet

1. Rapporter funn, ikke dom. "Avsnitt 2 har en ikke-X-men-Y-vending, p=0,91" er nyttig. "73 % AI" er det ikke.
2. Tilstedeværelse er ikke alvorlighet. slopcheck-forfatteren markerte ni kontrastvendinger som reelt til stede og samtidig "helt greie å publisere". Gaten må vekte etter sjanger og alvorlighet, og det gjør koden, ikke modellen.
3. En sjekkliste måler bare det som er der. Tom og ren tekst er verre enn litt AI-aktig tekst med innhold. Verktøyet trenger derfor også positive sjekker (del 2, gruppe G) og en "mangler"-rapport.
4. Mekanisk fjerning av alle tegn fjerner også stemmen. Kontrast, vurdering og tydelige påstander er ofte selve poenget. Hvert hint bør kunne svare "behold denne".
5. Norsk krever egne lister. De engelske ordlistene kan ikke oversettes direkte, de må valideres mot norsk korpus med samme metode som slop-forensics (del 4 og 8).

---

## 2. Katalog over kjennetegn

Kolonnen Lag sier hvem som bør avgjøre:

- `regex`: mønster eller ordliste, lokalt, gratis
- `stat`: beregnet mål (spaCy, telling, frekvensratio), lokalt
- `jev`: krever lesing, går til Jev som Noul
- `bank`: krever minne på tvers av tekster (frasebank)

Kolonnen Omfang: `avsn` kan vurderes per avsnitt, `dok` gir bare mening for hele teksten.

Norske ordlister nedenfor er hypoteser. De er satt sammen fra norske praktikerkilder og fra oversettelse av engelske mønstre, og skal valideres med frekvensratio mot korpus før de får gate-status.

### A. Ordvalg

| ID | Kjennetegn | Eksempler | Lag | Omfang |
| --- | --- | --- | --- | --- |
| A01 | Stilord som er overrepresentert i LLM-tekst (EN) | delve, tapestry, testament, underscore, pivotal, crucial, intricate, showcase, foster, garner, leverage, seamless, robust, landscape, realm, navigate, embark, vibrant, multifaceted, meticulous, boasts, interplay, enduring | regex | avsn |
| A02 | Tilsvarende på norsk | banebrytende, revolusjonerende, innovativ, sømløs, helhetlig, skreddersydd, avgjørende, sentral rolle, spiller en viktig rolle, vitner om, understreker, belyser, fremhever, fremmer, legger til rette for, i stadig endring, i dagens samfunn, i en verden der, verdifull innsikt, nøkkelen til, synergi, paradigmeskifte, landskap og reise brukt billedlig | regex + stat | avsn |
| A03 | Fyll- og skiltfraser | det er viktig å merke seg, det er verdt å nevne, la oss se nærmere på, la oss dykke ned i, la oss bryte det ned, kort sagt, med andre ord, alt i alt, til syvende og sist, når det kommer til | regex | avsn |
| A04 | Chatbot-rester | Håper dette hjelper, Gi meg beskjed hvis, Selvfølgelig!, Absolutt!, Godt spørsmål, Her er en oversikt:, Som en AI, henvisning til kunnskapsgrense, plassholdere som [Navn] | regex | dok |
| A05 | Forsterkere og oppriktighetsmarkører | ærlig talt, helt ærlig, virkelig, faktisk, utrolig, genuint, rett og slett, uten tvil | regex (tetthet) | avsn |
| A06 | Stablede forbehold | kan potensielt, vil muligvis kunne, i mange tilfeller ofte | regex for par, jev for skjønn | avsn |
| A07 | Omskriving av "er" | fungerer som, står som, representerer, utgjør, tjener som | jev | avsn |
| A08 | Oppblåst ord der et enkelt finnes | benytte, anvende, implementere, fasilitere, optimalisere, i forbindelse med, med hensyn til | regex | avsn |
| A09 | Smisk og terapitone | Det er helt forståelig, Du er ikke alene, Det er helt normalt å føle, Så bra at du spør | regex + jev | avsn |
| A10 | Abstrakte metafor-substantiv | reise, landskap, økosystem, verktøykasse, byggestein, bro, fundament, kompass | regex (tetthet) | avsn |
| A11 | Koblingsord i setningsstart, overbruk | Dessuten, I tillegg, Videre, Samtidig, Imidlertid, Derfor | stat (andel setninger) | dok |

A08 overlapper med klarspråk. Det er en fordel: Språkrådets klarspråkråd kan gjenbrukes som regelkilde.

### B. Tegnsetting, typografi og formatering

| ID | Kjennetegn | Merknad | Lag | Omfang |
| --- | --- | --- | --- | --- |
| B01 | Tankestrek-tetthet | Terskel per sjanger. Norsk tankestrek med mellomrom er normal bruk. Engelsk em dash uten mellomrom i norsk tekst er et sterkere tegn | regex | avsn |
| B02 | Kolon-avsløring | "Her er greia:", "Resultatet:", "Poenget: Alltid test." | regex for tetthet, jev for skjønn | avsn |
| B03 | Fet skrift-tetthet | Fet på vilkårlige fraser | regex | dok |
| B04 | Punktliste med fet etikett | "**Skalerbarhet:** Systemet skalerer." Etiketten gjentas ofte i setningen etter | regex | dok |
| B05 | Overskrifter og lister i kort tekst | Struktur som ikke står i forhold til lengden | stat | dok |
| B06 | Emoji som punktmerke eller overskrift | "🚌 Bussoppdatering:" | regex | dok |
| B07 | Title Case i norske overskrifter | Sterkt tegn på norsk, siden norsk bruker liten forbokstav | regex | dok |
| B08 | Komma foran "og" i oppramsing | Oxford-komma er en anglisisme | regex | avsn |
| B09 | Engelske anførselstegn i norsk tekst | " " der norsk har « ». Svakt tegn, mange mennesker gjør det samme | regex | dok |
| B10 | Komma etter foranstilt setningsadverb | "Imidlertid, det finnes", "I dag, mange bedrifter". Engelsk mønster, ofte sammen med brudd på V2 | regex + jev | avsn |
| B11 | Markdown i ren tekst-kanal | Stjerner og skigarder i SMS eller push-varsel | regex (kanalavhengig) | dok |
| B12 | Piler, skillelinjer, tabeller uten behov | | regex | dok |
| B13 | Særskriving og engelsk stor forbokstav | "kunde service", "Mandag", "Norsk" | regex + ordliste | avsn |
| B14 | Utropstegn-tetthet | | regex | dok |

### C. Setnings- og avsnittsstruktur

| ID | Kjennetegn | Eksempel eller beskrivelse | Lag | Omfang |
| --- | --- | --- | --- | --- |
| C01 | Negativ parallellisme | "Det er ikke bare et verktøy, det er en ny måte å jobbe på." "Det handler ikke om X. Det handler om Y." | jev | avsn |
| C02 | Tretall for rytmens skyld | "rask, trygg og enkel". Tre sideordnede ledd der to eller fire ville vært like sant | jev | avsn |
| C03 | Retorisk spørsmål med eget svar | "Resultatet? Færre feil." | jev | avsn |
| C04 | Oppsummerende eller aforistisk slutt | Siste setning sier avsnittet en gang til, eller lander på en visdom ("Til syvende og sist handler det om tillit.") | jev | avsn + dok |
| C05 | Oppsummeringsavslutning | "Oppsummert", "Alt i alt", et sluttavsnitt uten ny informasjon | regex + jev | dok |
| C06 | Halsrensk i åpningen | Gjentar spørsmålet, setter scenen ("I dagens digitale hverdag"), lover hva som kommer | jev | dok |
| C07 | Varslet struktur | "La oss se på tre grunner." Teksten snakker om seg selv | jev | avsn |
| C08 | Ensartet setningslengde | Lav variasjon i paragrafer på fire setninger eller mer | stat | avsn |
| C09 | Dramatiske fragmenter | "Enkelt. Effektivt. Trygt." | regex + jev | avsn |
| C10 | "Noe som"-hale | Hovedsetning pluss påhengt tolkning: "..., noe som understreker betydningen av ...", "... og bidrar dermed til ...". Norsk motstykke til engelske -ing-ledd | regex for kandidater, jev for skjønn | avsn |
| C11 | Nominaliseringstetthet | "gjennomføring av en vurdering av" | stat (spaCy) | avsn |
| C12 | Falske spenn | "alt fra små bedrifter til store konsern", der endepunktene ikke avgrenser noe | jev | avsn |
| C13 | Synonymkarusell | Samme ting kalles verktøyet, løsningen, plattformen, systemet for å unngå gjentakelse | jev | dok |
| C14 | Ensartede avsnitt | Alle avsnitt like lange, alle med samme bygning (påstand, utdyping, punchline) | stat + jev | dok |
| C15 | Utfordringer og fremtidsutsikter-formelen | "Til tross for utfordringer ... ser fremtiden lys ut" | jev | dok |
| C16 | Passiv som skjuler aktøren | "Det ble besluttet at" der leseren trenger å vite hvem | jev (støyende, høy terskel) | avsn |
| C17 | Parallellgitter | Alle punkter i en liste har samme syntaktiske form og lengde | stat | dok |
| C18 | Fraktal gjentakelse | Samme poeng i innledning, hoveddel og avslutning | jev | dok |

### D. Innhold og holdning

| ID | Kjennetegn | Beskrivelse | Lag | Omfang |
| --- | --- | --- | --- | --- |
| D01 | Generisk | Avsnittet kunne stått i en tekst om nesten hva som helst. Ingen navn, tall, datoer eller detaljer | jev | avsn |
| D02 | Betydningsoppblåsing | Et rutinefaktum gjøres til et vendepunkt eller del av en større utvikling | jev | avsn |
| D03 | Vag kildehenvisning | "studier viser", "eksperter mener", "mange opplever" | regex + jev | avsn |
| D04 | Reklametone i nøytral sjanger | | jev | avsn |
| D05 | Følelse i stedet for mekanisme | Sier hvordan noe oppleves, ikke hva det gjør | jev | avsn |
| D06 | Påklistret redaksjonell kommentar | "Det er viktig å huske at" | regex + jev | avsn |
| D07 | Begge-sider-unnvikelse | Tar ikke stilling når spørsmålet ba om det. "Det avhenger av flere faktorer" | jev | dok |
| D08 | Uforespurte forbehold og ansvarsfraskrivelser | "Rådfør deg med en fagperson" der ingen spurte | regex + jev | dok |
| D09 | Overforklaring | Definerer det leseren helt sikkert kan, svarer på mer enn det som ble spurt om | jev | dok |
| D10 | Meny-avslutning | "Vil du at jeg skal ...?", "Gi beskjed om du ønsker ..." | regex | dok |
| D11 | Jevn positivitet | Ingen kant, ingen humor, ingen irritasjon, alt er spennende | jev | dok |
| D12 | Moraliserende eller uforent visdom | Livsvisdom som ikke følger av innholdet | jev | dok |
| D13 | Mulig oppdiktet presisjon | Navn, tall og kilder som ser konkrete ut. Kan ikke verifiseres av en linter, men kan flagges som "krever sjekk" | jev (lav prioritet) | avsn |
| D14 | Skjønnlitterære klisjeer | Hjerter som hamrer, hvisking knapt hørbar, overbrukte navn. Bare relevant hvis fiksjon skal støttes | regex | avsn |

### E. Norskspesifikt

Språkrådets undersøkelser (2024 og 2025) fant at engelsk skinner gjennom i KI-generert norsk, at nynorsk er klart dårligere enn bokmål, og at vekslingen mellom radikale og konservative former virker umotivert.

| ID | Kjennetegn | Eksempler | Lag |
| --- | --- | --- | --- |
| E01 | Oversatte idiomer og kalker | tok et øyeblikk, i person, gjøre en forskjell, på slutten av dagen, adressere et problem, når det kommer til, har du noen gang lurt på | regex (liste) + jev ("lyder dette som oversatt engelsk?") |
| E02 | Engelsk leddstilling | Brudd på V2 etter foranstilt ledd, se B10 | jev |
| E03 | Stedsformat | "Gudbrandsdalen, Noreg" etter amerikansk mønster | regex |
| E04 | Umotivert formveksling | Blanding av -a og -en, radikale og konservative former uten system. På nynorsk: bokmålsnære former blandet med utpreget tradisjonelle | stat (ordliste over formpar) |
| E05 | Amerikansk entusiasme i du-form | Superlativer, utropstegn, "fantastisk", "elsker" | regex + jev |
| E06 | Preposisjonskalker | "på en daglig basis", "i form av", overbruk av "basert på" | regex |

### F. Kanal- og agentspesifikt

Disse gjelder korte meldinger fra agenter. De er sannsynligvis de mest nyttige for ditt oppsett.

| ID | Kjennetegn | Lag |
| --- | --- | --- |
| F01 | Lengde står ikke i forhold til innholdet (et varsel på over to setninger) | stat |
| F02 | Hilsen eller signatur i et push-varsel | regex |
| F03 | Det handlingsrettede faktumet kommer ikke først | jev |
| F04 | Meldingen gjentar det mottakeren allerede vet | jev (krever kontekst i state) |
| F05 | Samme formulering som forrige melding fra samme agent | bank |
| F06 | Etikett pluss kolon som åpning ("Oppdatering:") | regex |

### G. Positive signaler

Disse stilles som egne Noul-spørsmål og teller for teksten. De er motvekten mot at agenten optimaliserer seg til ren, tom tekst.

| ID | Signal |
| --- | --- |
| G01 | Inneholder minst én konkret detalj (navn, tall, tidspunkt, sted) som er relevant for poenget |
| G02 | Tar stilling der sjangeren ber om det |
| G03 | Første setning sier det viktigste |
| G04 | Registeret passer kanalen og mottakeren (oppgis i state) |
| G05 | Idiomatisk norsk |
| G06 | Teksten er fortsatt klar og naturlig (kjøres etter omskriving, for å fange overkorrigering) |

---

## 3. Hvordan skrive spørsmål til Jev

Fakta om modellen (verifiser mot docs.typesafe.ai før koding, grensene flytter seg):

- Tre primitiver: Noul (sannsynlighet for ja), Choice (1 til 255 alternativer), Score (2 til 10 nivåer).
- Endepunkt `https://api.typesafe.ai/v1/systemone`. Modell `jev-1.13.0`, aliasene `jev-latest` og `jev-preview`. Pin versjonsnummeret når terskler er tunet.
- 64k tokens totalt for state pluss alle spørsmål, 32k for state pluss lengste spørsmål.
- Ratebegrensning oppgitt til 1200 forespørsler per minutt og 250k tokens per sekund. SDK-ene har backoff.
- Alle spørsmål i et kall besvares parallelt og uavhengig. Svar A er ikke kontekst for spørsmål B.
- Offisielle ressurser: `typesafe-sdk-python`, `typesafe-sdk-js`, et agent-skill for spørsmålsdesign, og `system-one-adapter-python` som gir samme klientgrensesnitt mot en vanlig LLM slik at man kan sammenligne på identiske spørsmål.

Regler for spørsmålene, samlet fra dokumentasjonen og fra de to mest gjennomarbeidede prosjektene:

1. Formuler slik at høy sannsynlighet betyr ja. Et Noul der true betyr "nei" gir dårligere svar.
2. Ett skjønn per spørsmål. Ikke gjem flere vurderinger i samme spørsmål.
3. Ikke spør om noe kode kan telle.
4. Bruk `criteria` med true- og false-beskrivelse når grensen er subtil. Test med og uten.
5. Skriv `not_for`: nærliggende tilfeller som ikke skal flagges. snifftest kaller dette det som holder regelen ærlig. Uten det flagges ting du ikke mente.
6. Definer begrepet i spørsmålet. slopcheck fikk `hidden_actor_passive` fra p=0,51 til 0,90 ved å forklare hva passiv er, og `forced_triad` fra 0,22 til 0,86 ved å spørre om de tre leddene er sideordnede i stedet for om det tredje er "fyll".
7. Behandle 0,40 til 0,60 som "ingen vurdering". To uavhengige prosjekter landet på samme bånd av samme grunn: modellen svarer rundt 0,5 på tekst den ikke klarer å lese. Dette er særlig viktig på norsk.
8. Standardterskel 0,7, justerbar per regel. Støyende regler (passiv) trenger 0,8.
9. Ikke be om linjenummer for semantiske tegn. slopcheck fjernet linjelokalisering og gikk fra presisjon 0,80 til 0,95 og fra 1365 ms til 575 ms. Bruk i stedet avsnittsmodus: koden vet hvor avsnittet står.
10. Send avsnittskall samtidig, ikke etter hverandre. Det er forskjellen mellom 3,2 s og 0,7 s per dokument i slopchecks sammenligning.
11. Kjør både dokument- og avsnittsmodus når det er råd. De finner ulike ting. Dokumentmodus ser mønstre som går over avsnitt, avsnittsmodus ser ett dårlig avsnitt som ellers vannes ut.
12. Noen spørsmål gir bare mening for hele teksten (C04 kicker, C05, C06, C13). Hvert avsnitt har en første og en siste linje, så "er siste linje en aforisme" slår ut overalt hvis det spørres per avsnitt. Merk dem `scope: document`.
13. For Score: ikke rund av gjennomsnittet. Bruk fordelingen, og velg nivået med mest masse hvis du trenger ett nivå.
14. Tekst som omtaler et kjennetegn, blir flagget for å inneholde det. Fjern sitater og kodeblokker før sending, og godta at dette dokumentet selv vil slå ut.
15. State kan påvirkes av tekst som er skrevet for å styre modellen. Test med fiendtlig input før verktøyet brukes på andres tekst.

Åpent spørsmål som må testes: fungerer norske spørsmål om norsk tekst bedre enn engelske spørsmål om norsk tekst? Kjør begge på samme seed-sett i uke 1.

### Forslag til regelformat

Eget YAML-format, lånt fra snifftest og slopcheck. Filen er hele domenet. Kode og terskler er skilt fra spørsmålstekst.

```yaml
version: 1
model: jev-1.13.0
threshold: 0.7
no_judgment_band: [0.40, 0.60]

rules:
  - id: C01_negativ_parallellisme
    layer: jev
    scope: paragraph
    lang: [nb, nn, en]
    severity: 2            # 1 kosmetisk, 2 merkbar, 3 ødelegger tilliten
    genres_off: [debattinnlegg]
    what: |
      Minst én setning avviser en merkelapp bare for å erstatte den med en
      annen ("ikke bare X, men Y", "det handler ikke om X, det handler om Y"),
      der avvisningen ikke svarer på noe leseren faktisk trodde.
    not_for: |
      En reell korreksjon av en misforståelse som er nevnt tidligere i teksten.
      En saklig avgrensning ("gjelder ikke buss 510, bare 505").
    criteria:
      true: "Minst én setning har en kontrastvending som er pynt, ikke korreksjon."
      false: "Ingen kontrastvending, eller kontrasten retter en reell misforståelse."
    hint: "Si andre halvdel direkte og stryk første."
    keep_if: "Kontrasten er selve argumentet i teksten."

  - id: B07_title_case_no
    layer: regex
    scope: document
    lang: [nb, nn]
    severity: 1
    pattern: '^#{1,6}\s+(?:[A-ZÆØÅ][a-zæøå]+\s+){2,}[A-ZÆØÅ][a-zæøå]+'
    hint: "Norske overskrifter har stor forbokstav bare i første ord og egennavn."
```

`hint` og `keep_if` er faste tekster i koden. Jev kan ikke forklare seg, så regel-ID-en er forklaringen, og hintet er det agenten handler på.

---

## 4. Referansekorpus fra før 2022

Tre bruksområder, og de stiller ulike krav:

- **Frekvensbaseline** for å finne overrepresenterte ord og n-gram (stort, trenger ikke være pent).
- **Rene avsnitt** til seeded-fault-evaluering og falsk-positiv-måling (middelstort, må være i riktig sjanger).
- **Parvise data**: menneskelig tekst pluss LLM-fortsettelse av samme åpning (må genereres selv).

Sett en hard datogrense på 2022-11-30 (ChatGPT-lansering). Vær obs på at korpus "oppdatert etter" denne datoen kan være forurenet.

### Norsk

| Kilde | Hva | Periode | Egnet til | Merknad |
| --- | --- | --- | --- | --- |
| NoReC (`ltgoslo/norec`) | 35 000+ anmeldelser fra VG, Dagbladet, Aftenposten, NRK P3, DinSide m.fl. | 1998 til 2017 | Rene avsnitt, meningsbærende prosa med stemme | Beste enkeltkilde for "menneskelig kvalitet". Sjekk lisens for bruk |
| Norwegian Colossal Corpus (`NbAiLab/NCC` på Hugging Face) | Samling av mange norske korpus, 30 GB | Blandet | Frekvensbaseline | Avisdelen under Språkbank-avtalen ble trukket i desember 2024. Filtrer på dato og kilde |
| Norsk aviskorpus (Språkbanken, sbr-4) | 1,68 mrd. ord bokmål, 68 mill. nynorsk | 1998 til 2019 | Frekvensbaseline | Sjekk om nedlasting fortsatt er åpen. CC BY-NC |
| Stortingets referater (data.stortinget.no) | Taler og debatt, åpent API | Flere tiår | Muntlig-formell prosa, argumentasjon | Offentlig og fritt |
| NOU-er og stortingsmeldinger (regjeringen.no), Målfrid-korpuset | Forvaltningsprosa | Før 2022 | Negativ kontroll: menneskeskrevet, men stiv. Verktøyet skal ikke flagge dette som "AI", men gjerne som uklart | Viktig for å måle falske positiver |
| Norsk Wikipedia-dump | Leksikonprosa | Bruk dump fra 2021 eller filtrer på revisjonstid | Nøytral sakprosa | Dumper fra før 2022 finnes i arkiv |
| NoWaC (UiO Tekstlab) | Nettkorpus fra .no | 2009 til 2010 | Frekvensbaseline, blogg- og forumspråk | Eldre, men helt uforurenet |
| NorDial | Tweets med dialektmerking | ca. 2021 | Korte, uformelle meldinger | Lite, men riktig register for varsler |
| Reddit r/norge via Pushshift-dumper | Kommentarer | Til 2022 | Uformell dialog | Sjekk vilkår |
| Leksikografisk bokmålskorpus (LBK) | Balansert, inkl. skjønnlitteratur | Før 2013 | Referanse | Søkegrensesnitt, begrenset nedlasting |
| NDLA, forskning.no, NRK Ytring via Wayback Machine | Formidling og kronikker | Velg datoer før 2022 | Rene avsnitt i formidlingssjanger | Krever skraping, respekter vilkår |
| `wordfreq` (nb) | Ferdig frekvensliste | Snapshot til ca. 2021 | Rask baseline for A02-validering | Vedlikeholderen sluttet å oppdatere i 2024 nettopp på grunn av AI-forurening, så snapshotet er rent |

Det finnes ikke noe åpent norsk e-postkorpus. For korte agentmeldinger er egne gamle SMS-er og chatlogger fortsatt den beste kilden til riktig register, men de trenger bare dekke gruppe F. Resten dekkes av kildene over.

### Engelsk

| Kilde | Egnet til |
| --- | --- |
| Enron-korpuset | E-postregister |
| Pushshift Reddit-dumper (til 2022) | Uformell prosa, svar på spørsmål (samme sjanger som chatbot-svar) |
| StackExchange-dumper med dato | Tekniske svar skrevet av mennesker |
| Hacker News-datasett | Korte, meningsbærende kommentarer |
| Wikipedia-dump fra 2021 | Nøytral sakprosa |
| arXiv- og PubMed-abstracts før 2020 | Akademisk prosa (Matsui viser at driften startet i 2020) |
| OpenWebText (2019), C4 (2019), The Pile (2020) | Frekvensbaseline |
| Blog Authorship Corpus (2004) | Personlig stemme |
| `wordfreq` (en) | Rask baseline |

### Ferdige menneske-mot-maskin-datasett (engelsk)

HC3, RAID, MAGE og M4 har parvise eller merkede tekster. Nyttige til å teste ordlister, men laget for forfatterskapsdeteksjon. Modellene i dem er eldre enn dem agentene dine bruker.

### Slik lages den parvise norske delen

Følg metoden fra Reinhart m.fl.: ta et menneskeskrevet avsnitt, gi en LLM de første setningene og be den fortsette. Da er tema, sjanger og lengde kontrollert. Bruk minst tre modellfamilier, siden fingeravtrykkene er familiespesifikke. Lag også en variant der modellen er bedt om å skrive "uformelt og menneskelig", og en der et menneske har redigert lett. Det er de to gruppene der verktøy vanligvis svikter.

---

## 5. Andre verktøy og tilnærminger

### Regelbaserte prosa-lintere

| Verktøy | Hva | Norsk? | Vurdering |
| --- | --- | --- | --- |
| Vale | Regelmotor med YAML-stiler, språkuavhengig | Ja, med egne regler | Sterk kandidat som motor for regex-laget. Flere `vale-ai-tells`-pakker finnes (tbhb, krishnasunkam m.fl.) med svært spesifikke regler, bl.a. "Label: Setning"-kolon, formelavslutninger, menneskeliggjøring av verktøy ("spesifikasjonen vil ha") og "mekanisme, så slutning"-setninger |
| textlint | Pluggbar JS-linter | Ja, med egne regler | Alternativ til Vale hvis stacken er Node |
| proselint, write-good, alex | Engelske stilråd | Nei | Bare for engelsk tekst |
| nabokov (PyPI) | flake8-aktig linter med lesbarhet og AI-tegn, bygd på spaCy | Nei | God modell for regelkoder og for "flat rytme"-måling |
| unslopify (PyPI) | Linter pluss frasebank som husker tidligere formuleringer og feiler gjentakelse på tvers av svar | Språkuavhengig idé | Frasebanken er det mest originale her, og treffer F05 direkte |
| prose-sanitiser (Rust) | Deterministisk, med konfidensnivåer og publiserte måltall per regeltabell, fjerner også usynlig Unicode | Nei | Usynlig-Unicode-sjekken er verdt å ta med |
| LanguageTool | Grammatikk og stavekontroll | Svak dekning for norsk, sjekk status | Kan ta B13 og E-gruppen hvis dekningen holder |
| Klarspråk-ressurser fra Språkrådet | Råd og ordlister | Ja | Regelkilde for A08 og C11 |

### Statistiske mål (lokalt, uten modell)

- Setningslengde: standardavvik og variasjonskoeffisient per avsnitt (C08).
- LIX som lesbarhetsmål. Det er laget for skandinaviske språk og er enkelt å beregne.
- Ordvariasjon: MTLD eller glidende type/token-ratio.
- Nominaliseringsandel og passivandel via spaCy (`nb_core_news_md`).
- Andel setninger som åpner med koblingsord (A11).
- Overrepresentasjon: frekvensratio for ord, bigram og trigram mot baseline, etter slop-forensics-metoden. EQ-Bench Slop Score vekter slop-ord 60 % og bruker i tillegg "ikke X, men Y"-mønstre og slop-trigram. Forfatteren presiserer at dette måler overbrukte mønstre, ikke forfatterskap, og at det virker best på flere tekster samlet.

### Sannsynlighetsbaserte detektorer

GLTR, DetectGPT, Fast-DetectGPT og Binoculars måler hvor forutsigbar teksten er for en språkmodell. Kommersielle (GPTZero, Pangram, Originality) gjør varianter av det samme. De svarer på "hvem skrev dette", ikke "er dette godt", de er engelsksentrerte, og de har de dokumenterte falsk-positiv-problemene fra del 1. Anbefaling: ikke ta dem med i gaten. Eventuelt som et eksperimentelt lag bak en bryter.

### LLM som dommer

En frontier-modell med et langt stil-skill (unslop med 31 tegn, no-ai-slop, humanizer) er best på oppgaven. slopcheck målte Claude til presisjon 0,97 og recall 0,77 mot Jevs 0,95 og 0,47, men til 21 sekunder per tekst. snifftest målte Opus 5 til 77 av 80 plantede feil og 0 av 54 rene avsnitt flagget, mot Jevs 63 og 1, til omtrent 240 ganger kostnaden. Den billigste LLM-en (Haiku 4.5) fanget 66, men flagget 37 av 54 rene avsnitt. Det siste er det viktige: en billig LLM er ikke et alternativ til Jev her, den er dårligere på falske positiver.

Konklusjon: bruk LLM som eskaleringssteg og til omskriving, ikke som alltid-på-port.

---

## 6. Prior art med Jev på GitHub

Jev ble lansert 15. september 2026. På fem dager har det kommet over tjue awesome-lister og flere prosa-lintere. De to første nedenfor er gjennomarbeidede og har MIT-lisens.

### snifftest (DanRWilloughby/snifftest)

TypeScript, null avhengigheter. 5 tellbare regler lokalt, 10 skjønnsregler til Jev per avsnitt.

Verdt å låne:

- Regelformatet med `what`, `not_for`, `examples`, `criteria` og `message`, og at et prosjekt kan arve standardreglene og overstyre per ID.
- Ingen-vurdering-båndet 0,4 til 0,6, og exit-kode 2 når skjønnslaget ikke svarte på noe. Et flatt 0,5 er den ene feilen som ser ut som et rent utkast.
- Samtykkeflyten: verktøyet skriver ut nøyaktig hva som forlater maskinen før første sending. Relevant for deg, siden agentene håndterer lekser og familiens data.
- Cache nøklet på hash av avsnitt, eksakt spørsmålstekst og modellversjon. Avsnittet selv lagres aldri.
- `snifftest eval`: planter én kjent feil per regel i dine egne rene avsnitt og måler tre armer (ingen, tellbare, tellbare pluss Jev). `snifftest bench` stiller de samme spørsmålene til et panel av LLM-er.
- `--twins`: måler hva en setning skrevet for å lure sjekken gjør med avlesningene rundt.
- Ærlig rapportering: variasjonen mellom kjøringer (59 til 64 av 80 samme dag) oppgis som målestokken alle tall må leses mot.
- Markedsføringsregler som egen tagg, av som standard.

### slopcheck-jev (harshpuri84/slopcheck-jev)

Python. 18 regex-tegn, 15 Jev-Nouls i ett kall, gate i kode. Leveres som Claude Code Stop-hook som sjekker Claudes egne svar etter hver tur og advarer i stedet for å blokkere.

Verdt å låne:

- Tre lag med klart eierskap: Lex finner, Judge vurderer, Gate bestemmer. Modellen blir aldri spurt om et menneske bør bry seg. Det er policy, og policy ligger i kode.
- Dokument- og avsnittsmodus, med `scope: document` på de fire tegnene som ikke gir mening per avsnitt.
- Historien om hvorfor linjelokalisering ble fjernet, med tall. Spar deg for å gjenta eksperimentet.
- Dekningstabellen mot unslops 31 tegn, med lag per tegn. God sjekkliste mot katalogen i del 2.
- Pooled adjudication som evalueringsmetode, og regelen om at modellen ikke får skrive fasiten.
- Demosiden som viser alle femten sannsynligheter med terskel og ingen-vurdering-stripe. Nyttig under tuning.
- Den ærlige begrensningen: måler tilstedeværelse, ikke alvorlighet. Det er hullet dette prosjektet kan fylle med `severity` og sjangerprofiler.

### Andre verdt en titt

- **riff**: prosa-linter med ruff-aktige regelkoder.
- **taste-lint** (mblode): lokale sjekker pluss Jev, egne profiler for UI-tekst, Markdown og agentinstruksjoner. Ukalibrerte AI-regler forblir rådgivende.
- **JevSlop** (TKY-27): helhetsvurdering pluss åtte Score-akser i ett kall for japanske artikler. Relevant fordi det er ikke-engelsk, og fordi hovedetiketten er Jevs egen helhetsvurdering og ikke et snitt av aksene.
- **human-compiler**: diagnostikk for prosa i kompilatorstil.
- **vibecheck**: sjekk av innlegg før publisering.
- **tripwire**: AI SDK-mellomvare som kjører sju Jev-sjekker på hvert LLM-svar før brukeren ser det. Samme plassering som du ønsker for agentene.
- **jev-mcp** (blakestone-x og burnigtm) og **jev-use**: generelle MCP-servere for Jev. jev-use avviser spørsmål som ikke lar seg type før kallet, og merker lavkonfidente svar som "priors". Bruk som skjelett for MCP-delen.
- **huncho**: gjør Jev-svar om til navngitte beslutninger med inn- og ut-terskler (hysterese), nyttig for varslingsagentene dine uavhengig av dette prosjektet.
- **slop-linter** (almcc): samme idé for kode. Prinsippet om at dommeren bør være en annen modell enn forfatteren, gjelder også her.
- Oversikter: `hellogumbo/awesome-jev` (størst), `lukstei/awesome-jev-typesafe` (kuratert), `yibie/awesome-jev` (med måltall i beskrivelsene).

Ingen av prosjektene jeg fant, dekker norsk, og ingen kombinerer frasebank, sjangerprofiler og alvorlighetsvekting.

---

## 7. Foreslått arkitektur

```
tekst + sjanger + kanal + språk
        |
   [0] Forbehandling: fjern kode, sitater, front matter. Språkdeteksjon. Del i avsnitt.
        |
   [1] Lex: regex og ordlister (nb, nn, en)            lokalt, ca. 5 ms
   [2] Stat: rytme, LIX, nominalisering, n-gram-ratio  lokalt, ca. 50 ms med spaCy
   [3] Bank: sammenlign mot tidligere meldinger        lokalt, SQLite
        |
   [4] Jev: ett dokumentkall + ett kall per avsnitt, samtidig      ca. 0,6 til 1,5 s
        |
   [5] Gate (kode): terskler, ingen-vurdering-bånd, sjangerprofil, alvorlighetsvekt
        |
   [6] Valgfritt: eskalering til LLM når mange svar ligger i båndet, eller for omskriving
        |
   JSON ut
```

Lag 1 til 3 kjører alltid og sender ingenting ut. Lag 4 krever nøkkel og samtykke.

### MCP-verktøy

| Verktøy | Inn | Ut |
| --- | --- | --- |
| `check_text` | `text`, `genre`, `channel`, `lang?`, `mode` (`fast` uten Jev, `full`), `context?` (hva mottakeren allerede vet, for F04) | Se skjema under |
| `list_rules` | `genre?` | Regler i kraft med lag, terskel og kilde |
| `explain_rule` | `id` | `what`, `not_for`, eksempler, hint |
| `record_feedback` | `finding_id`, `verdict` (`riktig`, `feil`, `riktig_men_greit`) | Lagres for kalibrering |
| `bank_add` | `agent_id`, `text` | Legger godkjent melding i frasebanken |

`riktig_men_greit` er viktig. Det er dataene som gjør at alvorlighet kan læres per sjanger.

### Svarskjema

```json
{
  "verdict": "revise",
  "score": 0.41,
  "round": 1,
  "max_rounds": 2,
  "findings": [
    {
      "id": "f3",
      "rule": "C04_oppsummerende_slutt",
      "layer": "jev",
      "scope": "paragraph",
      "paragraph": 2,
      "p": 0.88,
      "severity": 2,
      "hint": "Stryk siste setning. Slutt på den tydeligste konkrete setningen som allerede står der.",
      "keep_if": "Setningen tilfører en ny opplysning."
    }
  ],
  "positives": {"G01_konkret_detalj": 0.22, "G03_poenget_forst": 0.81},
  "missing": ["Ingen konkret detalj (G01 under 0,4)"],
  "no_judgment": ["E02_engelsk_leddstilling"],
  "meta": {"model": "jev-1.13.0", "ms": 742, "jev_calls": 4, "lang": "nb"}
}
```

`verdict` er `pass`, `revise` eller `pass_with_notes`. Etter `max_rounds` returneres alltid `pass_with_notes`, slik at agenten ikke går i sløyfe.

### Sjangerprofiler

En profil slår regler av og på og setter terskler og vekter. Forslag til start:

- `varsel`: gruppe F på, B03 til B06 strenge, D-gruppen av, makslengde.
- `melding`: uformell tekst til familie. A09 og E05 strenge.
- `epost`: halsrensk, meny-avslutning og chatbot-rester strenge.
- `sakprosa`: hele katalogen, standardterskler.
- `debatt`: C01, C02 og D06 av eller rådgivende. Kontrast og vurdering er sjangeren.
- `teknisk`: B-gruppen løsere (lister og kode er normalt), D09 strengere.

### Vern mot at agenten optimaliserer mot sjekken

- Tak på to omskrivingsrunder.
- G06 ("fortsatt klar og naturlig") kjøres etter hver omskriving.
- Positive signaler må over terskel for `pass`, ikke bare fravær av funn.
- Frasebanken fanger at agenten bytter ett mønster mot et annet fast mønster.
- Hintene er faste tekster og sier hva som skal ut, ikke hva som skal inn. Da får ikke agenten en ny formel å gjenta.

### Personvern

- Lekser og familiemeldinger er persondata. Be om Zero Data Retention og No Training per forespørsel der gatewayen støtter det (Vercel AI Gateway oppgir at Jev støtter begge).
- `mode: fast` skal være fullverdig nok til at sensitive tekster kan sjekkes uten å sendes.
- Cache nøkles på hash. Teksten lagres ikke.

---

## 8. Evalueringsplan

1. **Seeded faults** (fra snifftest). Ta 200 rene norske avsnitt fra korpus i riktig sjanger. Plant én kjent feil per regel i kopier, åtte til ti per regel. Feilene kan genereres av en LLM, men et menneske godkjenner hver. Mål fanget andel per regel, og flaggede rene avsnitt.
2. **Negativ kontroll**. Kjør NOU-utdrag, stortingsreferater og NoReC-anmeldelser. Dette er menneskeskrevet tekst i stiv, muntlig og meningsbærende form. Mål falsk-positiv-rate per regel per sjanger. En regel som flagger over 5 % av rene avsnitt, blir rådgivende til den er omskrevet.
3. **Parvise data** (del 4). Samme åpning, menneskelig og LLM-fortsettelse, tre modellfamilier. Mål om totalscoren skiller parene, og hvilke regler som bærer forskjellen.
4. **Kalibrering**. Reliabilitetsdiagram per regel: er funn med p rundt 0,8 riktige rundt 80 % av gangene? Kalibrering er en egenskap ved grupper av svar og er målt på TypeSafes data, ikke dine. Den må etterprøves på norsk.
5. **Spørsmålsspråk**. Samme regler formulert på norsk og engelsk, samme seeds.
6. **Pooled adjudication** (fra slopcheck) på ekte agentmeldinger. Alle lag kjører, unionen av funn blir en pulje, du markerer hver rad uten å se hvilket lag som flagget. Modellen skriver aldri fasiten. Recall er recall mot puljen.
7. **Bench mot LLM** med `system-one-adapter-python` på identiske spørsmål, for å vite hva den billige porten går glipp av.
8. **Oppgi alltid n og variasjon mellom kjøringer.** Tun på et utviklingssett og hold et testsett urørt.

Ordlistevalidering (A02, E01): beregn frekvensratio mellom egen-generert norsk LLM-tekst og baseline (wordfreq nb pluss NCC-utvalg). Behold ord med høy ratio og tilstrekkelig antall forekomster. Dropp resten, uansett hvor AI-aktige de føles.

---

## 9. Arbeidsrekkefølge

1. Les `docs.typesafe.ai` (primitiver, grenser, Python-SDK) og installer det offisielle agent-skillet for spørsmålsdesign. Klon snifftest og slopcheck-jev og les `rules/default.yaml` og `slopcheck/tells.yaml`.
2. Sett opp repo: Python, FastMCP, `rules/*.yaml`, `profiles/*.yaml`, `bench/`.
3. Lag 0 og 1: forbehandling og regex-regler for gruppe A, B og F. `mode: fast` virker nå uten nøkkel.
4. Hent korpus: NoReC, wordfreq nb, et NCC-utvalg, stortingsreferater. Bygg baseline-frekvenser.
5. Generer parvise norske data med tre modellfamilier. Valider A02 og E01 med frekvensratio.
6. Lag 2: rytme, LIX, nominalisering, koblingsord.
7. Lag 4: start med ti Jev-regler med høyest forventet nytte: C01, C02, C04, C06, C10, D01, D02, D05, E01 og G01. Dokument- og avsnittsmodus, samtidige kall, cache, ingen-vurdering-bånd.
8. Seeded-fault-eval og negativ kontroll. Omskriv spørsmål som leser under 0,6 på plantede feil. Test norsk mot engelsk spørsmålstekst.
9. Gate, sjangerprofiler og alvorlighetsvekter. `record_feedback`.
10. Lag 3: frasebank i SQLite (shingles på fem til åtte ord per agent).
11. Koble på én agent (bussvarsel) med `varsel`-profilen. Logg alt i to uker, gjør pooled adjudication, juster terskler.
12. Utvid regelsettet fra katalogen etter hva adjudiceringen viser at mangler.

---

## 10. Kilder

Forskning:

- Reinhart m.fl., "Do LLMs write like humans? Variation in grammatical and rhetorical styles", PNAS 122(8), 2025. https://doi.org/10.1073/pnas.2422455122
- Kobak m.fl., "Delving into LLM-assisted writing in biomedical publications through excess vocabulary", Science Advances 11(27), 2025. https://doi.org/10.1126/sciadv.adt3813
- Matsui, "Delving Into PubMed Records", Perspectives on Medical Education 14(1), 2025. https://pmejournal.org/articles/10.5334/pme.1929
- Liang m.fl., "GPT detectors are biased against non-native English writers", Patterns 4(7), 2023. https://doi.org/10.1016/j.patter.2023.100779
- Weber-Wulff m.fl., "Testing of detection tools for AI-generated text", Int. J. for Educational Integrity 19(26), 2023. https://link.springer.com/article/10.1007/s40979-023-00146-z
- Brooks m.fl., "The Rise of AI-Generated Content in Wikipedia", WikiNLP 2024. https://aclanthology.org/2024.wikinlp-1.12.pdf
- Paech m.fl., "Antislop", ICLR 2026. https://arxiv.org/pdf/2510.15061
- Freeburg, "The Last Fingerprint", arXiv:2603.27006, 2026 (preprint, ikke fagfellevurdert). https://arxiv.org/abs/2603.27006

Feltguider og norske kilder:

- Wikipedia: Signs of AI writing. https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
- Språkrådet, "KI-språkets fallgruver" (2024). https://sprakradet.no/aktuelt/ki-sprakets-fallgruver/
- Språkrådet, rapport om språket i KI-genererte tekster (oktober 2025), omtalt hos https://aiavisen.no/rapport-chatboter-stryker-i-norsk/
- Kommunikasjonsforeningen, "Skriver du ChatGPTsk?". https://www.kommunikasjon.no/fagstoff/guider-og-maler/2025/skriver-du-chatgptsk-slik-unngar-du-a-hore-robotisk-ut

Jev og TypeSafe:

- Dokumentasjon: https://docs.typesafe.ai/primitives/noul
- Flavio Copes, gjennomgang av Jev: https://flaviocopes.com/jev/
- Praktisk guide (DEV): https://dev.to/valyuai/how-to-use-jev-a-practical-guide-to-typesafes-system-one-model-g5e
- Fire feil med primitivene (DEV): https://dev.to/dave8172/choice-score-and-noul-four-mistakes-with-jevs-primitives-1eng
- Vercel AI Gateway: https://vercel.com/changelog/typesafe-ai-jev-now-available-on-ai-gateway

Prior art:

- https://github.com/DanRWilloughby/snifftest
- https://github.com/harshpuri84/slopcheck-jev
- https://github.com/TKY-27/JevSlop
- https://github.com/mblode/taste-lint
- https://github.com/almcc/slop-linter
- https://github.com/hellogumbo/awesome-jev
- https://github.com/lukstei/awesome-jev-typesafe
- https://github.com/yibie/awesome-jev

Andre verktøy:

- https://github.com/sam-paech/slop-forensics
- https://github.com/sam-paech/auto-antislop
- https://eqbench.com/slop-score.html
- https://github.com/tbhb/vale-ai-tells
- https://github.com/krishnasunkam/vale-ai-tells
- https://pypi.org/project/unslopify/
- https://pypi.org/project/nabokov/
- https://github.com/DreamLab-AI/prose-sanitiser
- https://github.com/aihxp/humanizer

Korpus:

- NoReC: https://github.com/ltgoslo/norec
- NCC: https://huggingface.co/datasets/NbAiLab/NCC
- Norsk aviskorpus: https://www.nb.no/sprakbanken/en/resource-catalogue/oai-nb-no-sbr-4/

Forbehold: tallene fra snifftest og slopcheck er forfatternes egne, på små utvalg (80 plantede feil, 45 adjudiserte rader). TypeSafes ytelsestall er selvrapporterte. Jev er fem dager gammel, og API-grenser endres uten varsel. De norske ordlistene i del 2 er ikke validert.
