# Vyhodnocení skeneru 2026-11-23 08:10 UTC

Náklady: poplatek 0.1 % + skluz 0.05 % na stranu (≈ 0.30 % ceny za celý obchod). Výsledky v R po nákladech.

## Odeslané signály (6)

- BTC/USDT 1h short 2026-10-24T16:00 (stop 0.21 %): stop, -2.44 R za 1 svíček
- ETH/USDT 1d short 2026-10-29T00:00 (stop 8.03 %): stop, -1.04 R za 6 svíček
- SOL/USDT 1d short 2026-10-29T00:00 (stop 8.68 %): time, +2.29 R za 20 svíček
- XRP/USDT 1d short 2026-10-29T00:00 (stop 13.56 %): time, +1.78 R za 20 svíček
- DOGE/USDT 1d short 2026-10-29T00:00 (stop 8.48 %): time, +2.27 R za 20 svíček
- SOL/USDT 1d short 2026-11-05T00:00 (stop 10.49 %): open, +1.88 R za 18 svíček

Uzavřené: {'n': 5, 'win': 60.0, 'avg_r': 0.573, 'ci': 1.909, 'sum_r': 2.86, 'max_dd_r': 1.04}

## Verdikty desku vs. výsledek

| Skupina | Uzavřené obchody | Win % | Ø R | Σ R |
|---|---|---|---|---|
| schváleno (A/B) | 0 | 0.0 | +0.000 | +0.00 |
| zamítnuto (C/NO_TRADE) | 5 | 60.0 | +0.573 | +2.86 |
| bez verdiktu | 0 | 0.0 | +0.000 | +0.00 |

Desk přidává hodnotu, jen když „schváleno (A/B)“ dlouhodobě vychází lépe než „zamítnuto“.

## Backtest aktuálního nastavení (BTC/USDT 17448 svíček, ETH/USDT 17445 svíček, SOL/USDT 17447 svíček, XRP/USDT 17448 svíček, ADA/USDT 17445 svíček, LINK/USDT 17445 svíček, AVAX/USDT 17445 svíček, DOGE/USDT 17446 svíček)

| | Obchody | Win % | Ø R (95% CI) | Σ R | Max DD (R) | Náhodné Ø R | Výhoda |
|---|---|---|---|---|---|---|---|
| BTC/USDT | 118 | 39.0 | -0.038 ± 0.274 | -4.5 | 14.76 | -0.293 | +0.255 |
| ETH/USDT | 116 | 40.5 | +0.137 ± 0.331 | +15.8 | 17.93 | -0.191 | +0.328 |
| SOL/USDT | 141 | 37.6 | +0.128 ± 0.314 | +18.0 | 15.96 | -0.207 | +0.335 |
| XRP/USDT | 113 | 37.2 | +0.033 ± 0.316 | +3.7 | 15.26 | -0.123 | +0.156 |
| ADA/USDT | 114 | 35.1 | +0.019 ± 0.345 | +2.1 | 20.4 | -0.091 | +0.110 |
| LINK/USDT | 99 | 38.4 | +0.103 ± 0.379 | +10.2 | 13.66 | -0.169 | +0.272 |
| AVAX/USDT | 114 | 34.2 | +0.183 ± 0.385 | +20.9 | 23.23 | -0.149 | +0.332 |
| DOGE/USDT | 124 | 28.2 | -0.023 ± 0.349 | -2.9 | 28.8 | -0.126 | +0.103 |
| **celkem** | 939 | 36.2 | +0.068 ± 0.119 | +63.4 | 98.88 | -0.170 | +0.238 |
| in-sample 70 % | 703 | 34.4 | +0.036 ± 0.139 | +25.6 | 78.51 | -0.120 | +0.156 |
| out-of-sample 30 % | 236 | 41.5 | +0.160 ± 0.228 | +37.8 | 20.78 | -0.265 | +0.425 |

## Strategie (celá historie, in-sample 70 % / out-of-sample 30 %)

| Strategie | Obchody | Ø R celkem | IS Ø R | OOS Ø R (95% CI) | Náhodné (OOS) |
|---|---|---|---|---|---|
| donchian_1d | 632 | +0.393 | +0.481 | +0.153 ± 0.205 | +0.084 |
| pullback_1d | 648 | +0.296 | +0.382 | +0.136 ± 0.199 | +0.098 |

## Hypotéza H3 – `skip_weekends: true` (research/knowledge.md)

Předem stanovená varianta: zvlášť pro donchian_1d a pullback_1d jen `skip_weekends: true`, ostatní parametry beze změny.
Stejná metodika jako tabulka „Strategie“ (IS/OOS 70/30, náhodné vstupy, náklady z config). Výsledky v R po nákladech.

| Strategie | Varianta | IS n | IS Ø R | OOS n | OOS Ø R (95% CI) | Náhodné (OOS) | OOS 1. pol. | OOS 2. pol. | Mince lepší (OOS) |
|---|---|---|---|---|---|---|---|---|---|
| donchian_1d | dnes | 463 | +0.481 | 169 | +0.153 ± 0.205 | +0.084 | +0.071 | +0.250 | – |
| donchian_1d | skip_weekends | 405 | +0.466 | 147 | +0.255 ± 0.220 | +0.095 | +0.242 | +0.282 | 8 / 8 |
| pullback_1d | dnes | 430 | +0.382 | 219 | +0.136 ± 0.199 | +0.098 | +0.200 | +0.080 | – |
| pullback_1d | skip_weekends | 388 | +0.360 | 196 | +0.200 ± 0.198 | +0.098 | +0.222 | +0.184 | 7 / 8 |

Kritéria hypotézy (OOS ≥ 100 obchodů, OOS +≥ 0,05 R, výhoda nad náhodou) splněna u obou strategií
(Donchian +0,10 R, pullback +0,06 R), ale **in-sample je u obou horší** (−0,015 a −0,022 R) – podmínka změny configu
„in-sample není horší“ splněna není. Navíc podezření vzniklo 25. 10. 2026 právě z tohoto OOS úseku (stejná data) a za
celých 10 let víkendové vstupy horší nebyly. Rozdíly jsou hluboko uvnitř 95% CI.
**Výsledek: neprošla – config beze změny.** Zopakovat jen na nových datech (obchody od 26. 10. 2026).

## Závěr kontroly

- Obě zapnuté strategie mají OOS Ø R > 0 a porážejí náhodné vstupy (Donchian +0,153 vs. +0,084, pullback +0,136 vs. +0,098),
  ale výhoda je uvnitř 95% CI → ponechat zapnuté, nic nevypínat.
- Desk: všech 5 uzavřených signálů mělo verdikt C/NO_TRADE (+0,57 R/obchod, Σ +2,86 R); A/B zatím 0 – nelze srovnat.
- Kalibrace scénářů (2022–2026, neutrální střed): pod medvědím 11–12 %, nad mediánem 45–46 %, nad býčím 6–7 % – v pásmu.
- Config beze změny (H3 neprošla na podmínce in-sample). Nejde o finanční poradenství.
