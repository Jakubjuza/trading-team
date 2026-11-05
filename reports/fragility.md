# 🧊 Křehkost trhu a pozdní vstup – výsledky testu

Spuštěno 2026-11-05 18:35 UTC. Pravidla stanovena předem (hlavička `research/experiments/fragility_test.py`). Index: `research/fragility.py`.
Denní strategie donchian_1d + pullback_1d, 8 mincí, 1271 obchodů (2016-12 – 2026-10), náklady 0,15 %/stranu. Šoků BTC (≥ 3σ za hodinu): 328 (2024-11 – 2026-11).

## T1 Křehkost: **NEPROŠLO ❌**

1. pol.: proti +0,191 vs. ostatní +0,116 (rozdíl -0,075); 2. pol.: proti -0,348 vs. ostatní +0,198 (rozdíl +0,547); n = 59

| obchod vůči stavu | n | Ø R | 1. pol. Ø R (n) | 2. pol. Ø R (n) | výhry | vypláchnuto ≥ 0,5 R proti |
|---|---|---|---|---|---|---|
| proti | 59 | -0,038 | +0,191 (34) | -0,348 (25) | 47 % | 73 % |
| po směru | 81 | +0,356 | +0,454 (54) | +0,159 (27) | 51 % | 63 % |
| vyrovnaný / málo dat | 142 | +0,047 | -0,243 (51) | +0,210 (91) | 38 % | 75 % |

Po směru a stavu (Ø R, n):

| stav BTC | long | short |
|---|---|---|
| křehký | +0,365 (15) | +0,434 (43) |
| vyrovnaný | -0,537 (38) | +0,248 (101) |
| optimistický | +0,267 (38) | -0,175 (44) |
| málo dat | +1,532 (2) | -1,032 (1) |

BTC za 7 dní po stavu (denní vzorky, Ø %; vzorky se překrývají – jen popis):

| stav | dní | Ø % | 1. pol. | 2. pol. | podíl dní |
|---|---|---|---|---|---|
| křehký | 127 | -0,66 | -0,50 | -0,92 | 19 % |
| vyrovnaný | 385 | -0,06 | +0,17 | -0,22 | 58 % |
| optimistický | 146 | +0,35 | +0,14 | +0,67 | 22 % |
| málo dat | 3 | +3,47 | – | +3,47 | 0 % |

Rozhodnutí Fedu (FOMC, 14:00 New York) v datech: pohyb BTC 4 h a 24 h po prohlášení a K před ním:

| datum | K před | stav | 4 h % | 24 h % |
|---|---|---|---|---|
| 2025-01-29 | -0,01 | vyrovnaný | +0,12 | +2,08 |
| 2025-03-19 | +0,08 | vyrovnaný | +0,49 | -1,96 |
| 2025-05-07 | -0,35 | optimistický | +0,72 | +5,00 |
| 2025-06-18 | -0,26 | optimistický | +1,12 | +0,66 |
| 2025-07-30 | -0,43 | optimistický | +0,77 | +0,91 |
| 2025-09-17 | +0,18 | vyrovnaný | +1,33 | +2,28 |
| 2025-10-29 | +0,30 | křehký | -0,01 | -3,75 |
| 2025-12-10 | +0,28 | křehký | -0,99 | -2,31 |
| 2026-01-28 | -0,03 | vyrovnaný | -0,29 | -6,22 |
| 2026-03-18 | -0,35 | optimistický | +0,21 | -1,62 |
| 2026-04-29 | +0,09 | vyrovnaný | +0,54 | +1,10 |
| 2026-06-17 | +0,33 | křehký | -1,87 | -4,33 |
| 2026-07-29 | -0,38 | optimistický | -0,88 | +0,33 |
| 2026-09-16 | -0,68 | optimistický | +0,09 | +1,26 |
| 2026-10-28 | -0,20 | vyrovnaný | +0,31 | -0,21 |

## T2 Pozdní vstup (přetažení od EMA20): **NEPROŠLO ❌**

1. pol.: ≥ 2 ATR +0,730 vs. ostatní +0,520 (rozdíl -0,210); 2. pol.: ≥ 2 ATR +0,241 vs. ostatní +0,128 (rozdíl -0,113); n = 444

| přetažení na signálu | n | Ø R | 1. pol. Ø R (n) | 2. pol. Ø R (n) | výhry | vypláchnuto ≥ 0,5 R proti |
|---|---|---|---|---|---|---|
| < 1 ATR | 419 | +0,232 | +0,526 (150) | +0,068 (269) | 40 % | 71 % |
| 1–2 ATR | 408 | +0,299 | +0,513 (140) | +0,188 (268) | 47 % | 65 % |
| ≥ 2 ATR | 444 | +0,475 | +0,730 (213) | +0,241 (231) | 53 % | 61 % |

Pohyb signálního dne ve směru obchodu (popis):

| pohyb dne | n | Ø R | 1. pol. Ø R (n) | 2. pol. Ø R (n) | výhry | vypláchnuto ≥ 0,5 R proti |
|---|---|---|---|---|---|---|
| < 0,5 ATR | 215 | +0,253 | +0,572 (88) | +0,032 (127) | 40 % | 68 % |
| 0,5–1,5 ATR | 784 | +0,294 | +0,556 (298) | +0,134 (486) | 47 % | 65 % |
| ≥ 1,5 ATR | 272 | +0,533 | +0,770 (117) | +0,354 (155) | 54 % | 66 % |

Po strategiích (Ø R):

| strategie | < 1 ATR | 1–2 ATR | ≥ 2 ATR |
|---|---|---|---|
| donchian_1d | -1,027 (2) | +0,265 (248) | +0,481 (376) |
| pullback_1d | +0,238 (417) | +0,353 (160) | +0,444 (68) |

## Stav teď

⚖️ Křehkost trhu K +0.15 (vyrovnaný, před týdnem -0.20) · šoky 30 dní 7↓/7↑ · dotažení špatných -0.02, dobrých -0.45

Rozhodnutí: co PROŠLO, jde nejdřív papírově souběžně (jako vstup z nižších TF); co NEPROŠLO, zůstává jen popisem pro desk. Pravidla skeneru se mění jen po testu.

Nejde o finanční poradenství.
