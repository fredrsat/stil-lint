# Seeded-fault-evaluering: 10 rene avsnitt per regel

Feilene er plantet med faste maler (én per regel). Avsnittene er
uflaggede NoReC-avsnitt fra negativ kontroll.

## Regex-/statregler, mode=fast

| regel | plantede | fanget | andel | ingen-vurdering | andre funn/tekst |
| --- | --- | --- | --- | --- | --- |
| A02_stilord_nb | 10 | 10 | 100% | 0 | 0.1 |
| A03_skiltfraser | 10 | 10 | 100% | 0 | 0.1 |
| A04_chatbotrester | 10 | 10 | 100% | 0 | 0.0 |
| A05_forsterkere | 10 | 10 | 100% | 0 | 0.1 |
| A09_smisk | 10 | 10 | 100% | 0 | 0.0 |
| A12_llm_ngram_validert | 10 | 10 | 100% | 0 | 0.1 |
| B01_tankestrek | 10 | 9 | 90% | 0 | 0.0 |
| B02_kolonavsloring | 10 | 10 | 100% | 0 | 0.0 |
| C09_dramatiske_fragmenter | 10 | 10 | 100% | 0 | 0.0 |
| C10_noe_som_hale | 10 | 10 | 100% | 0 | 0.1 |
| D03_vag_kilde | 10 | 10 | 100% | 0 | 0.0 |
| D10_menyavslutning | 10 | 10 | 100% | 0 | 0.0 |
| E03_stedsformat | 10 | 10 | 100% | 0 | 0.0 |
| E06_preposisjonskalker | 10 | 10 | 100% | 0 | 0.0 |

## Jev-regler, norsk spørsmålstekst (mode=full)

| regel | plantede | fanget | andel | ingen-vurdering | andre funn/tekst |
| --- | --- | --- | --- | --- | --- |
| C01_negativ_parallellisme | 10 | 10 | 100% | 0 | 0.6 |
| C02_tvunget_tretall | 10 | 10 | 100% | 0 | 0.7 |
| C04_oppsummerende_slutt | 10 | 10 | 100% | 0 | 0.4 |
| C06_halsrensk | 10 | 10 | 100% | 0 | 2.2 |
| C10_pahengt_tolkning | 10 | 10 | 100% | 0 | 1.4 |
| D02_betydningsoppblasing | 10 | 8 | 80% | 1 | 0.8 |
| D05_folelse_ikke_mekanisme | 10 | 8 | 80% | 0 | 0.3 |
| E01_oversatt_engelsk | 10 | 7 | 70% | 0 | 1.8 |

## Jev-regler, engelsk spørsmålstekst (mode=full)

| regel | plantede | fanget | andel | ingen-vurdering | andre funn/tekst |
| --- | --- | --- | --- | --- | --- |
| C01_negativ_parallellisme | 10 | 10 | 100% | 0 | 0.4 |
| C02_tvunget_tretall | 10 | 0 | 0% | 1 | 0.1 |
| C04_oppsummerende_slutt | 10 | 6 | 60% | 1 | 0.3 |
| C06_halsrensk | 10 | 10 | 100% | 0 | 2.3 |
| C10_pahengt_tolkning | 10 | 10 | 100% | 0 | 1.2 |
| D02_betydningsoppblasing | 10 | 8 | 80% | 1 | 0.7 |
| D05_folelse_ikke_mekanisme | 10 | 0 | 0% | 3 | 0.1 |
| E01_oversatt_engelsk | 10 | 3 | 30% | 5 | 1.9 |

Merk: n er lite; les andeler mot variasjon mellom kjøringer, jf.
researchdokumentets forbehold. Cache gjør at re-kjøring med samme
tekster og spørsmål gir identiske tall.
