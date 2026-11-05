# Vyhodnocení skeneru 2026-11-05 08:10 UTC

Náklady: poplatek 0.1 % + skluz 0.05 % na stranu (≈ 0.30 % ceny za celý obchod). Výsledky v R po nákladech.

## Odeslané signály (5)

- BTC/USDT 1h short 2026-10-24T16:00 (stop 0.21 %): stop, -2.44 R za 2 svíček
- ETH/USDT 1d short 2026-10-29T00:00 (stop 8.03 %): stop, -1.04 R za 6 svíček
- SOL/USDT 1d short 2026-10-29T00:00 (stop 8.68 %): open, -0.07 R za 7 svíček
- XRP/USDT 1d short 2026-10-29T00:00 (stop 13.56 %): open, -0.49 R za 7 svíček
- DOGE/USDT 1d short 2026-10-29T00:00 (stop 8.48 %): open, -0.21 R za 7 svíček

Uzavřené: {'n': 2, 'win': 0.0, 'avg_r': -1.74, 'ci': 1.374, 'sum_r': -3.48, 'max_dd_r': 1.04}

## Verdikty desku vs. výsledek

| Skupina | Uzavřené obchody | Win % | Ø R | Σ R |
|---|---|---|---|---|
| schváleno (A/B) | 0 | 0.0 | +0.000 | +0.00 |
| zamítnuto (C/NO_TRADE) | 2 | 0.0 | -1.740 | -3.48 |
| bez verdiktu | 0 | 0.0 | +0.000 | +0.00 |

Desk přidává hodnotu, jen když „schváleno (A/B)“ dlouhodobě vychází lépe než „zamítnuto“.

## Backtest aktuálního nastavení (BTC/USDT 17448 svíček, ETH/USDT 17445 svíček, SOL/USDT 17447 svíček, XRP/USDT 17448 svíček, ADA/USDT 17445 svíček, LINK/USDT 17445 svíček, AVAX/USDT 17445 svíček, DOGE/USDT 17446 svíček)

| | Obchody | Win % | Ø R (95% CI) | Σ R | Max DD (R) | Náhodné Ø R | Výhoda |
|---|---|---|---|---|---|---|---|
| BTC/USDT | 118 | 39.0 | -0.071 ± 0.266 | -8.4 | 14.76 | -0.233 | +0.162 |
| ETH/USDT | 115 | 39.1 | +0.086 ± 0.328 | +9.9 | 17.93 | -0.232 | +0.318 |
| SOL/USDT | 141 | 36.9 | +0.126 ± 0.316 | +17.8 | 15.96 | -0.173 | +0.299 |
| XRP/USDT | 111 | 36.9 | +0.027 ± 0.319 | +3.0 | 16.46 | -0.143 | +0.170 |
| ADA/USDT | 115 | 34.8 | +0.002 ± 0.341 | +0.2 | 20.39 | -0.138 | +0.140 |
| LINK/USDT | 99 | 38.4 | +0.137 ± 0.388 | +13.6 | 13.66 | -0.111 | +0.248 |
| AVAX/USDT | 116 | 33.6 | +0.207 ± 0.396 | +24.1 | 23.23 | -0.114 | +0.321 |
| DOGE/USDT | 127 | 27.6 | -0.072 ± 0.336 | -9.2 | 28.8 | -0.150 | +0.078 |
| **celkem** | 942 | 35.7 | +0.054 ± 0.119 | +50.9 | 98.88 | -0.163 | +0.217 |
| in-sample 70 % | 693 | 35.5 | +0.081 ± 0.142 | +56.2 | 69.72 | -0.142 | +0.223 |
| out-of-sample 30 % | 250 | 36.0 | -0.026 ± 0.212 | -6.5 | 50.09 | -0.283 | +0.257 |

## Strategie (celá historie, in-sample 70 % / out-of-sample 30 %)

| Strategie | Obchody | Ø R celkem | IS Ø R | OOS Ø R (95% CI) | Náhodné (OOS) |
|---|---|---|---|---|---|
| donchian_1d | 626 | +0.391 | +0.497 | +0.145 ± 0.206 | +0.050 |
| pullback_1d | 645 | +0.288 | +0.380 | +0.151 ± 0.207 | +0.031 |


## Hypotéza H3 (skip_weekends, denní strategie) – 5. 11. 2026

| Strategie | skip_weekends | IS Ø R | OOS n | OOS Ø R ± CI | Náhodné OOS | OOS 1. / 2. půlka |
|---|---|---|---|---|---|---|
| donchian_1d | ne (dnes) | +0,497 | 172 | +0,145 ± 0,206 | +0,050 | +0,085 / +0,248 |
| donchian_1d | ano | +0,479 | 149 | +0,231 ± 0,223 | +0,048 | +0,227 / +0,262 |
| pullback_1d | ne (dnes) | +0,380 | 220 | +0,151 ± 0,207 | +0,031 | +0,266 / +0,058 |
| pullback_1d | ano | +0,363 | 197 | +0,187 ± 0,200 | +0,054 | +0,286 / +0,111 |

Výsledek: **neprošla**. Donchian: zlepšení +0,086 R, ale in-sample je horší (−0,018) a v 2. půlce OOS jen +0,014 R; pullback: +0,036 R < 0,05 R. Config beze změny.
