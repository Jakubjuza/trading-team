# IFVG (inverse fair value gap, ICT) – bez mozku a s mozkem

Přepočet 2026-11-18 12:15 UTC. Pravidla stanovená předem jsou v hlavičce `research/experiments/ifvg_study.py`; po spuštění se nic neladilo. Jen výzkum, nic se nezapíná. Nejde o finanční poradenství.

**Vzor:** FVG = mezera mezi knoty 1. a 3. svíčky. IFVG long = medvědí mezera, kterou cena zavře nahoru (překlopí se v podporu); short = zrcadlo. Vstup hned po překlopení, nebo až na retestu zóny.

**Mozek:** *fáze* = vstup jen ve fázi trhu BTC, kde vzor v minulosti (IS) vydělával (pravidlo Dispečera); *kontext* = skóre z 14 metrik u signálu (mj. jestli průrazy na trhu pokračují, nebo jsou to fake outy), vstup jen nad 40. percentilem; *mozek* = obojí. Učení jen z IS (do 12/2023), test na OOS (1/2024–6/2025) a HOLDOUT (7/2025–dnes).

- 12h: 192 kombinací, 4 s, F&G ano, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 15m: 192 kombinací, 2743 s, F&G ano, data od BTC 01/2022, ETH 01/2022, SOL 01/2022, XRP 01/2022, ADA 01/2022, LINK 01/2022, AVAX 01/2022, DOGE 01/2022
- 1d: 192 kombinací, 3 s, F&G ano, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 1h: 192 kombinací, 12 s, F&G ano, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 2h: 192 kombinací, 6 s, F&G ano, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 4h: 192 kombinací, 4 s, F&G ano, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 6h: 192 kombinací, 6 s, F&G ano, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 1344 kombinací. Poplatky MEXC futures 0,05 %/stranu (rozhoduje). R = výsledek po poplatcích / riziko.

## 1. Funguje IFVG sám o sobě? (bez mozku)

| TF | Směr | Kombinací | OOS > 0 | HOLDOUT > 0 | Obě nad p95 náhody | Medián OOS R | Medián HOLDOUT R | Medián obch./měs. |
|---|---|---|---|---|---|---|---|---|
| 15m | long | 96 | 0 % | 1 % | 5 % | -0,11 | -0,14 | 230 |
| 15m | short | 96 | 1 % | 12 % | 6 % | -0,06 | -0,09 | 312 |
| 1h | long | 96 | 40 % | 30 % | 0 % | -0,02 | -0,05 | 54 |
| 1h | short | 96 | 66 % | 27 % | 0 % | +0,04 | -0,02 | 61 |
| 2h | long | 96 | 73 % | 23 % | 0 % | +0,06 | -0,09 | 25 |
| 2h | short | 96 | 72 % | 62 % | 8 % | +0,06 | +0,03 | 29 |
| 4h | long | 96 | 79 % | 34 % | 0 % | +0,10 | -0,10 | 12 |
| 4h | short | 96 | 74 % | 71 % | 8 % | +0,04 | +0,07 | 14 |
| 6h | long | 96 | 75 % | 32 % | 0 % | +0,10 | -0,10 | 9 |
| 6h | short | 96 | 54 % | 96 % | 4 % | +0,01 | +0,09 | 10 |
| 12h | long | 96 | 59 % | 38 % | 0 % | +0,07 | -0,06 | 4 |
| 12h | short | 96 | 32 % | 97 % | 4 % | -0,04 | +0,22 | 5 |
| 1d | long | 96 | 60 % | 58 % | 3 % | +0,05 | +0,05 | 2 |
| 1d | short | 96 | 4 % | 92 % | 0 % | -0,26 | +0,29 | 2 |

## 2. Pomáhá mozek? (stejné kombinace, Ø R v OOS / HOLDOUT)

„Lepší v obou“ = podíl kombinací, kde má brána v OOS i HOLDOUTU vyšší Ø R než stejná kombinace bez mozku (bez výhody ~25 %). „Ponecháno“ = medián podílu obchodů, které mozek pustí (OOS).

| TF | Směr | Bez mozku OOS / HOLD | Fáze OOS / HOLD | lepší v obou | Kontext OOS / HOLD | lepší v obou | Mozek OOS / HOLD | lepší v obou | ponecháno |
|---|---|---|---|---|---|---|---|---|---|
| 15m | long | -0,11 / -0,14 | -0,10 / -0,19 | 2 % | -0,04 / -0,18 | 16 % | -0,03 / -0,38 | 0 % | 0 % |
| 15m | short | -0,06 / -0,09 | -1,33 / -0,16 | 0 % | -0,06 / -0,09 | 0 % | -1,33 / -0,16 | 0 % | 0 % |
| 1h | long | -0,02 / -0,05 | +0,03 / -0,03 | 30 % | -0,02 / -0,03 | 42 % | -0,01 / -0,08 | 17 % | 22 % |
| 1h | short | +0,04 / -0,02 | +0,16 / -0,06 | 23 % | +0,00 / -0,08 | 9 % | +0,15 / -0,10 | 18 % | 1 % |
| 2h | long | +0,06 / -0,09 | -0,00 / -0,01 | 20 % | +0,15 / -0,13 | 35 % | +0,06 / -0,06 | 30 % | 30 % |
| 2h | short | +0,06 / +0,03 | +0,12 / +0,00 | 22 % | -0,01 / -0,03 | 5 % | +0,12 / -0,06 | 17 % | 18 % |
| 4h | long | +0,10 / -0,10 | +0,09 / -0,02 | 23 % | +0,10 / -0,10 | 0 % | +0,09 / -0,02 | 23 % | 41 % |
| 4h | short | +0,04 / +0,07 | +0,23 / +0,06 | 26 % | +0,05 / +0,07 | 27 % | +0,27 / +0,12 | 28 % | 12 % |
| 6h | long | +0,10 / -0,10 | +0,11 / +0,01 | 33 % | +0,21 / -0,14 | 49 % | +0,22 / -0,03 | 47 % | 32 % |
| 6h | short | +0,01 / +0,09 | +0,03 / +0,22 | 29 % | -0,01 / +0,07 | 17 % | +0,03 / +0,23 | 26 % | 16 % |
| 12h | long | +0,07 / -0,06 | +0,10 / -0,09 | 27 % | +0,15 / -0,13 | 15 % | +0,15 / -0,08 | 20 % | 39 % |
| 12h | short | -0,04 / +0,22 | +0,25 / +0,45 | 44 % | -0,11 / +0,16 | 4 % | +0,50 / +0,45 | 40 % | 5 % |
| 1d | long | +0,05 / +0,05 | +0,18 / +0,25 | 15 % | +0,05 / +0,05 | 0 % | +0,18 / +0,25 | 15 % | 36 % |
| 1d | short | -0,26 / +0,29 | -0,21 / +0,46 | 17 % | -0,26 / +0,29 | 0 % | -0,21 / +0,46 | 17 % | 1 % |

## 3. Předem stanovený výběr (10 nejlepších podle IS t na směr, pro každou variantu mozku)

**bez mozku** – prošlo 0 z 20 (a ze všech 1074 způsobilých kombinací by kritéria splnilo 3).

| Kombinace | IS n / Ø R / t | OOS n / Ø R / t | HOLDOUT n / Ø R | úspěšnost OOS | max. propad R | obch./měs. | Prošlo |
|---|---|---|---|---|---|---|---|
| 6h long · zóna ≥ 0,0 ATR · W 30 · retest · none · trail | 1112 / +0,46 / +5,1 | 423 / +0,31 / +1,6 | 402 / -0,06 | 32 % | 90 | 21,9 | ❌ |
| 6h long · zóna ≥ 0,0 ATR · W 30 · hned · none · trail | 1290 / +0,40 / +5,0 | 477 / +0,30 / +1,9 | 496 / -0,11 | 36 % | 126 | 25,5 | ❌ |
| 1h long · zóna ≥ 0,5 ATR · W 30 · retest · d50 · opp | 1026 / +0,63 / +4,9 | 260 / +0,02 / +0,1 | 223 / +0,26 | 44 % | 89 | 17,0 | ❌ |
| 12h long · zóna ≥ 0,0 ATR · W 10 · hned · none · trail | 594 / +0,62 / +4,9 | 235 / +0,49 / +1,4 | 201 / -0,22 | 31 % | 64 | 11,6 | ❌ |
| 6h long · zóna ≥ 0,0 ATR · W 30 · hned · none · opp | 1591 / +0,32 / +4,8 | 582 / +0,28 / +3,2 | 595 / +0,02 | 42 % | 99 | 31,2 | ❌ |
| 1h long · zóna ≥ 0,5 ATR · W 30 · hned · d50 · opp | 1236 / +0,54 / +4,7 | 303 / +0,15 / +0,7 | 267 / +0,01 | 43 % | 165 | 20,4 | ❌ |
| 1h long · zóna ≥ 0,0 ATR · W 30 · retest · d50 · trail | 3456 / +0,15 / +4,6 | 1132 / -0,12 / -2,8 | 818 / +0,10 | 30 % | 204 | 61,0 | ❌ |
| 2h long · zóna ≥ 0,0 ATR · W 30 · hned · d50 · trail | 1989 / +0,23 / +4,6 | 646 / +0,00 / +0,0 | 501 / +0,04 | 31 % | 101 | 35,4 | ❌ |
| 12h long · zóna ≥ 0,0 ATR · W 30 · retest · none · trail | 552 / +0,84 / +4,6 | 217 / +0,51 / +1,4 | 190 / -0,26 | 27 % | 73 | 10,8 | ❌ |
| 6h long · zóna ≥ 0,0 ATR · W 10 · hned · none · opp | 1284 / +0,34 / +4,6 | 447 / +0,30 / +2,8 | 482 / -0,07 | 43 % | 125 | 25,0 | ❌ |
| 1h short · zóna ≥ 0,5 ATR · W 30 · hned · d50 · trail | 1699 / +0,13 / +2,6 | 566 / +0,15 / +1,8 | 666 / +0,00 | 35 % | 89 | 33,1 | ❌ |
| 1h short · zóna ≥ 0,5 ATR · W 30 · hned · d200 · trail | 1598 / +0,11 / +2,3 | 437 / +0,08 / +1,0 | 758 / -0,01 | 36 % | 61 | 31,5 | ❌ |
| 12h short · zóna ≥ 0,0 ATR · W 30 · hned · d200 · opp_stop | 411 / +0,16 / +2,2 | 128 / -0,03 / -0,3 | 223 / +0,13 | 35 % | 41 | 8,6 | ❌ |
| 2h short · zóna ≥ 0,5 ATR · W 10 · hned · d200 · opp_stop | 469 / +0,28 / +2,1 | 136 / -0,21 / -1,4 | 232 / -0,07 | 23 % | 104 | 9,4 | ❌ |
| 2h short · zóna ≥ 0,5 ATR · W 30 · hned · d200 · opp_stop | 745 / +0,20 / +2,0 | 206 / -0,03 / -0,2 | 371 / +0,09 | 25 % | 72 | 14,9 | ❌ |
| 12h short · zóna ≥ 0,0 ATR · W 30 · retest · d200 · opp_stop | 328 / +0,15 / +2,0 | 111 / -0,02 / -0,2 | 177 / +0,01 | 37 % | 29 | 7,0 | ❌ |
| 6h short · zóna ≥ 0,5 ATR · W 10 · hned · d200 · trail | 163 / +0,26 / +1,9 | 59 / -0,09 / -0,5 | 109 / +0,18 | 36 % | 23 | 3,7 | ❌ |
| 2h short · zóna ≥ 0,5 ATR · W 30 · retest · d50 · trail | 565 / +0,15 / +1,9 | 217 / +0,07 / +0,6 | 251 / +0,25 | 34 % | 48 | 11,7 | ❌ |
| 1h short · zóna ≥ 0,5 ATR · W 30 · retest · d50 · trail | 1336 / +0,10 / +1,9 | 442 / +0,10 / +1,2 | 499 / -0,05 | 34 % | 82 | 25,7 | ❌ |
| 12h short · zóna ≥ 0,0 ATR · W 30 · retest · d200 · opp | 309 / +0,13 / +1,9 | 108 / -0,04 / -0,4 | 168 / -0,03 | 42 % | 22 | 6,6 | ❌ |

**mozek: fáze trhu** – prošlo 1 z 20 (a ze všech 555 způsobilých kombinací by kritéria splnilo 6).

| Kombinace | IS n / Ø R / t | OOS n / Ø R / t | HOLDOUT n / Ø R | úspěšnost OOS | max. propad R | obch./měs. | Prošlo |
|---|---|---|---|---|---|---|---|
| 1d long · zóna ≥ 0,0 ATR · W 30 · hned · none · target | 159 / +0,50 / +5,4 | 66 / +0,18 / +1,2 | 43 / -0,01 | 52 % | 20 | 3,0 | ❌ |
| 12h long · zóna ≥ 0,0 ATR · W 30 · retest · none · target | 302 / +0,36 / +5,1 | 101 / -0,31 / -2,8 | 63 / -0,42 | 28 % | 76 | 5,3 | ❌ |
| 12h long · zóna ≥ 0,0 ATR · W 10 · hned · none · trail | 386 / +0,90 / +5,0 | 203 / +0,62 / +1,6 | 138 / -0,05 | 33 % | 42 | 8,2 | ❌ |
| 12h long · zóna ≥ 0,0 ATR · W 30 · hned · none · target | 206 / +0,41 / +4,9 | 124 / -0,09 / -0,8 | 65 / +0,14 | 39 % | 32 | 4,5 | ❌ |
| 1h long · zóna ≥ 0,0 ATR · W 10 · retest · d50 · opp | 2159 / +0,17 / +4,8 | 808 / -0,02 / -0,4 | 355 / +0,19 | 36 % | 101 | 37,5 | ❌ |
| 12h long · zóna ≥ 0,0 ATR · W 10 · hned · none · target | 180 / +0,42 / +4,8 | 116 / -0,05 / -0,5 | 61 / +0,15 | 41 % | 30 | 4,0 | ❌ |
| 6h long · zóna ≥ 0,0 ATR · W 30 · retest · none · trail | 767 / +0,56 / +4,7 | 346 / +0,32 / +1,4 | 290 / -0,01 | 32 % | 76 | 15,8 | ❌ |
| 12h short · zóna ≥ 0,5 ATR · W 30 · hned · none · target | 141 / +0,46 / +4,7 | 33 / +0,50 / +2,4 | 64 / +0,46 | 64 % | 13 | 2,7 | ❌ |
| 6h long · zóna ≥ 0,0 ATR · W 30 · hned · none · opp | 908 / +0,52 / +4,7 | 370 / +0,23 / +2,2 | 320 / +0,15 | 40 % | 76 | 18,0 | ❌ |
| 4h short · zóna ≥ 0,0 ATR · W 30 · hned · none · opp_stop | 491 / +0,46 / +4,7 | 252 / +0,21 / +2,2 | 230 / +0,04 | 36 % | 46 | 11,0 | ❌ |
| 6h long · zóna ≥ 0,0 ATR · W 30 · hned · none · trail | 870 / +0,51 / +4,7 | 398 / +0,28 / +1,5 | 349 / -0,03 | 36 % | 99 | 18,2 | ❌ |
| 12h long · zóna ≥ 0,0 ATR · W 30 · hned · d50 · target | 114 / +0,51 / +4,6 | 41 / -0,35 / -2,0 | 23 / +0,29 | 29 % | 21 | 2,0 | ❌ |
| 1h short · zóna ≥ 0,5 ATR · W 30 · hned · none · trail | 1240 / +0,28 / +4,6 | 295 / +0,33 / +2,4 | 492 / -0,02 | 32 % | 68 | 22,9 | ❌ |
| 4h short · zóna ≥ 0,0 ATR · W 10 · hned · none · opp_stop | 416 / +0,46 / +4,6 | 206 / +0,22 / +2,0 | 193 / -0,05 | 37 % | 40 | 9,2 | ❌ |
| 6h short · zóna ≥ 0,0 ATR · W 30 · hned · none · opp_stop | 351 / +0,51 / +4,5 | 160 / +0,45 / +3,8 | 159 / +0,06 | 46 % | 26 | 7,6 | ❌ |
| 1h short · zóna ≥ 0,5 ATR · W 10 · hned · none · trail | 852 / +0,33 / +4,2 | 204 / +0,44 / +2,6 | 350 / -0,12 | 34 % | 71 | 15,9 | ❌ |
| 6h short · zóna ≥ 0,0 ATR · W 30 · hned · none · opp | 300 / +0,43 / +4,2 | 143 / +0,39 / +3,8 | 144 / +0,04 | 51 % | 21 | 6,6 | ❌ |
| 12h short · zóna ≥ 0,0 ATR · W 30 · hned · none · opp_stop | 345 / +0,35 / +4,1 | 86 / +0,28 / +2,3 | 155 / +0,34 | 52 % | 32 | 6,6 | ✅ |
| 4h short · zóna ≥ 0,0 ATR · W 30 · hned · none · trail | 336 / +0,48 / +4,1 | 163 / +0,49 / +3,9 | 165 / +0,03 | 46 % | 52 | 7,5 | ❌ |
| 4h short · zóna ≥ 0,0 ATR · W 10 · hned · none · trail | 304 / +0,47 / +4,1 | 146 / +0,52 / +4,0 | 155 / +0,02 | 47 % | 46 | 6,8 | ❌ |

**mozek: kontext signálu** – prošlo 0 z 20 (a ze všech 1136 způsobilých kombinací by kritéria splnilo 1).

| Kombinace | IS n / Ø R / t | OOS n / Ø R / t | HOLDOUT n / Ø R | úspěšnost OOS | max. propad R | obch./měs. | Prošlo |
|---|---|---|---|---|---|---|---|
| 6h long · zóna ≥ 0,0 ATR · W 30 · retest · none · trail | 561 / +0,74 / +5,1 | 181 / +0,21 / +1,1 | 174 / -0,11 | 28 % | 51 | 10,3 | ❌ |
| 1h long · zóna ≥ 0,0 ATR · W 30 · retest · d50 · trail | 2021 / +0,19 / +4,8 | 677 / -0,06 / -1,1 | 519 / +0,24 | 31 % | 107 | 36,3 | ❌ |
| 2h long · zóna ≥ 0,5 ATR · W 10 · hned · none · opp | 530 / +1,32 / +4,8 | 164 / +2,01 / +2,7 | 177 / -0,77 | 51 % | 172 | 9,8 | ❌ |
| 12h long · zóna ≥ 0,0 ATR · W 30 · retest · none · target | 336 / +0,31 / +4,6 | 108 / -0,19 / -1,7 | 103 / -0,25 | 32 % | 60 | 6,2 | ❌ |
| 12h long · zóna ≥ 0,0 ATR · W 30 · hned · none · opp | 515 / +0,51 / +4,5 | 182 / +0,33 / +2,1 | 190 / +0,04 | 42 % | 36 | 10,0 | ❌ |
| 4h long · zóna ≥ 0,0 ATR · W 30 · retest · none · trail | 1644 / +0,26 / +4,4 | 597 / +0,05 / +0,7 | 576 / +0,05 | 35 % | 93 | 31,8 | ❌ |
| 2h long · zóna ≥ 0,0 ATR · W 10 · retest · d50 · opp | 876 / +0,31 / +4,3 | 273 / +0,11 / +0,9 | 216 / +0,07 | 39 % | 42 | 15,4 | ❌ |
| 1h long · zóna ≥ 0,5 ATR · W 30 · hned · d50 · opp | 756 / +0,64 / +4,3 | 208 / +0,16 / +0,6 | 185 / -0,03 | 40 % | 140 | 13,0 | ❌ |
| 2h long · zóna ≥ 0,0 ATR · W 30 · hned · d50 · trail | 1217 / +0,30 / +4,3 | 398 / +0,02 / +0,2 | 306 / +0,12 | 31 % | 93 | 21,7 | ❌ |
| 12h long · zóna ≥ 0,0 ATR · W 10 · hned · none · opp | 392 / +0,51 / +4,3 | 141 / +0,39 / +2,2 | 140 / -0,12 | 43 % | 38 | 7,6 | ❌ |
| 1h short · zóna ≥ 0,5 ATR · W 30 · hned · d200 · trail | 930 / +0,20 / +3,0 | 262 / -0,01 / -0,1 | 386 / -0,12 | 31 % | 86 | 17,8 | ❌ |
| 1h short · zóna ≥ 0,5 ATR · W 30 · retest · d200 · trail | 727 / +0,21 / +2,8 | 202 / -0,03 / -0,3 | 293 / -0,16 | 31 % | 70 | 13,8 | ❌ |
| 12h short · zóna ≥ 0,0 ATR · W 10 · retest · none · opp_stop | 368 / +0,21 / +2,6 | 67 / -0,12 / -0,9 | 143 / +0,10 | 24 % | 27 | 6,5 | ❌ |
| 12h short · zóna ≥ 0,0 ATR · W 30 · hned · none · opp_stop | 573 / +0,16 / +2,6 | 104 / -0,06 / -0,7 | 237 / +0,20 | 37 % | 41 | 10,3 | ❌ |
| 12h short · zóna ≥ 0,0 ATR · W 30 · retest · none · opp_stop | 449 / +0,17 / +2,6 | 88 / -0,13 / -1,3 | 172 / +0,02 | 31 % | 33 | 8,0 | ❌ |
| 1h short · zóna ≥ 0,5 ATR · W 30 · retest · none · trail | 1728 / +0,10 / +2,5 | 478 / +0,04 / +0,5 | 429 / -0,09 | 31 % | 86 | 29,7 | ❌ |
| 12h short · zóna ≥ 0,5 ATR · W 30 · hned · none · target | 162 / +0,23 / +2,4 | 31 / +0,45 / +2,2 | 87 / +0,21 | 65 % | 19 | 3,2 | ❌ |
| 12h short · zóna ≥ 0,0 ATR · W 30 · hned · d200 · trail | 230 / +0,25 / +2,4 | 50 / -0,17 / -1,4 | 118 / +0,39 | 40 % | 27 | 4,5 | ❌ |
| 12h short · zóna ≥ 0,0 ATR · W 10 · hned · none · opp_stop | 496 / +0,16 / +2,4 | 95 / -0,05 / -0,4 | 206 / +0,26 | 36 % | 36 | 9,0 | ❌ |
| 12h short · zóna ≥ 0,0 ATR · W 30 · hned · d200 · opp_stop | 366 / +0,20 / +2,4 | 73 / -0,15 / -1,3 | 206 / +0,15 | 29 % | 41 | 7,3 | ❌ |

**mozek: fáze + kontext** – prošlo 0 z 20 (a ze všech 461 způsobilých kombinací by kritéria splnilo 1).

| Kombinace | IS n / Ø R / t | OOS n / Ø R / t | HOLDOUT n / Ø R | úspěšnost OOS | max. propad R | obch./měs. | Prošlo |
|---|---|---|---|---|---|---|---|
| 1d long · zóna ≥ 0,0 ATR · W 30 · hned · none · target | 159 / +0,50 / +5,4 | 66 / +0,18 / +1,2 | 43 / -0,01 | 52 % | 20 | 3,0 | ❌ |
| 12h long · zóna ≥ 0,0 ATR · W 30 · retest · none · target | 198 / +0,44 / +5,1 | 62 / -0,32 / -2,3 | 36 / -0,26 | 26 % | 38 | 3,3 | ❌ |
| 6h long · zóna ≥ 0,0 ATR · W 30 · retest · none · trail | 394 / +0,83 / +4,4 | 157 / +0,34 / +1,6 | 123 / +0,05 | 31 % | 31 | 7,6 | ❌ |
| 1h short · zóna ≥ 0,5 ATR · W 30 · retest · d50 · target | 178 / +0,39 / +4,4 | 89 / -0,25 / -2,1 | 60 / -0,09 | 34 % | 37 | 3,7 | ❌ |
| 1h long · zóna ≥ 0,5 ATR · W 30 · hned · d50 · opp | 506 / +0,87 / +4,4 | 192 / +0,13 / +0,5 | 128 / -0,16 | 40 % | 99 | 9,3 | ❌ |
| 1d long · zóna ≥ 0,0 ATR · W 10 · hned · none · target | 135 / +0,45 / +4,3 | 60 / +0,18 / +1,1 | 37 / -0,12 | 52 % | 19 | 2,6 | ❌ |
| 2h long · zóna ≥ 0,5 ATR · W 10 · hned · none · opp | 234 / +2,08 / +4,2 | 88 / +2,45 / +2,1 | 69 / -0,36 | 52 % | 110 | 4,4 | ❌ |
| 6h short · zóna ≥ 0,0 ATR · W 30 · hned · none · opp | 205 / +0,56 / +4,2 | 84 / +0,46 / +3,4 | 92 / +0,07 | 51 % | 12 | 4,3 | ❌ |
| 1h long · zóna ≥ 0,0 ATR · W 30 · retest · d50 · opp | 1478 / +0,15 / +4,2 | 570 / -0,01 / -0,2 | 283 / +0,24 | 36 % | 81 | 26,3 | ❌ |
| 2h long · zóna ≥ 0,0 ATR · W 10 · retest · d50 · opp | 478 / +0,47 / +4,2 | 205 / -0,10 / -0,8 | 115 / -0,12 | 38 % | 43 | 9,0 | ❌ |
| 4h long · zóna ≥ 0,0 ATR · W 30 · retest · none · trail | 939 / +0,37 / +4,2 | 440 / -0,02 / -0,2 | 390 / +0,11 | 32 % | 93 | 20,0 | ❌ |
| 12h long · zóna ≥ 0,0 ATR · W 10 · hned · none · trail | 189 / +0,75 / +4,2 | 91 / +0,59 / +1,6 | 66 / -0,27 | 32 % | 24 | 3,9 | ❌ |
| 2h short · zóna ≥ 0,0 ATR · W 30 · hned · none · trail | 463 / +0,47 / +4,1 | 233 / +0,49 / +3,5 | 219 / -0,03 | 41 % | 63 | 10,3 | ❌ |
| 6h short · zóna ≥ 0,0 ATR · W 30 · hned · none · opp_stop | 235 / +0,63 / +4,1 | 92 / +0,47 / +2,9 | 100 / +0,14 | 45 % | 18 | 4,8 | ❌ |
| 4h short · zóna ≥ 0,0 ATR · W 30 · hned · none · opp_stop | 317 / +0,53 / +4,1 | 153 / +0,24 / +1,7 | 138 / +0,11 | 33 % | 24 | 6,9 | ❌ |
| 6h short · zóna ≥ 0,0 ATR · W 30 · hned · none · trail | 146 / +0,74 / +4,1 | 64 / +0,48 / +2,5 | 56 / +0,28 | 56 % | 21 | 3,0 | ❌ |
| 1h short · zóna ≥ 0,5 ATR · W 30 · hned · none · trail | 715 / +0,34 / +4,0 | 183 / +0,41 / +2,2 | 250 / -0,08 | 33 % | 44 | 13,0 | ❌ |
| 4h short · zóna ≥ 0,0 ATR · W 10 · hned · none · opp_stop | 271 / +0,49 / +4,0 | 127 / +0,21 / +1,4 | 114 / -0,03 | 33 % | 27 | 5,8 | ❌ |
| 2h short · zóna ≥ 0,0 ATR · W 10 · hned · none · trail | 423 / +0,46 / +3,9 | 209 / +0,45 / +3,1 | 200 / +0,01 | 39 % | 55 | 9,4 | ❌ |
| 6h short · zóna ≥ 0,0 ATR · W 10 · hned · none · trail | 180 / +0,60 / +3,8 | 72 / +0,30 / +1,7 | 64 / +0,23 | 46 % | 22 | 3,6 | ❌ |

## 4. Co se mozek naučil (kontext, IS)

Metriky s váhou ≠ 0 (|t| ≥ 2): + = vyšší hodnota pomáhá, − = škodí. Prázdné = kontext nic spolehlivého nenašel.

- **15m** · short: — · long: + síla trendu ADX, + uklidnění před signálem, − nálada (strach/chamtivost)
- **1h** · short: − uklidnění před signálem · long: + uklidnění před signálem
- **2h** · short: − uklidnění před signálem · long: + objem průrazu, + přetažení od EMA20
- **4h** · short: + denní trend BTC, + boční pila (chop), + poloha v rozpětí 30 dní · long: —
- **6h** · short: + denní trend BTC, − trendovost (denní), + boční pila (chop), + poloha v rozpětí 30 dní, − uklidnění před signálem, + nálada (strach/chamtivost) · long: + přetažení od EMA20
- **12h** · short: + nálada (strach/chamtivost) · long: + přetažení od EMA20
- **1d** · short: — · long: —

## Závěr

✅ **Předem stanovené pravidlo splnilo:** 12h short · zóna ≥ 0,0 ATR · W 30 · hned · none · opp_stop (mozek: fáze trhu). Další krok je papírové ověření v laboratoři, ne ostré zapnutí.

Celá tabulka: `reports/ifvg/<timeframe>.csv.gz`. Nejde o finanční poradenství.