# Vyhodnocení skeneru 2026-11-02 08:20 UTC

Náklady: poplatek 0.1 % + skluz 0.05 % na stranu (≈ 0.30 % ceny za celý obchod). Výsledky v R po nákladech.

## Odeslané signály (5)

- BTC/USDT 1h short 2026-10-24T16:00 (stop 0.21 %): stop, -2.44 R za 2 svíček
- ETH/USDT 1d short 2026-10-29T00:00 (stop 8.03 %): open, -0.20 R za 4 svíček
- SOL/USDT 1d short 2026-10-29T00:00 (stop 8.68 %): open, +0.15 R za 4 svíček
- XRP/USDT 1d short 2026-10-29T00:00 (stop 13.56 %): open, -0.08 R za 4 svíček
- DOGE/USDT 1d short 2026-10-29T00:00 (stop 8.48 %): open, +0.01 R za 4 svíček

Uzavřené: {'n': 1, 'win': 0.0, 'avg_r': -2.441, 'ci': 0.0, 'sum_r': -2.44, 'max_dd_r': 0.0}

## Verdikty desku vs. výsledek

| Skupina | Uzavřené obchody | Win % | Ø R | Σ R |
|---|---|---|---|---|
| schváleno (A/B) | 0 | 0.0 | +0.000 | +0.00 |
| zamítnuto (C/NO_TRADE) | 1 | 0.0 | -2.441 | -2.44 |
| bez verdiktu | 0 | 0.0 | +0.000 | +0.00 |

Desk přidává hodnotu, jen když „schváleno (A/B)“ dlouhodobě vychází lépe než „zamítnuto“.

## Backtest aktuálního nastavení (BTC/USDT 17448 svíček, ETH/USDT 17445 svíček, SOL/USDT 17447 svíček, XRP/USDT 17448 svíček, ADA/USDT 17445 svíček, LINK/USDT 17445 svíček, AVAX/USDT 17445 svíček, DOGE/USDT 17446 svíček)

| | Obchody | Win % | Ø R (95% CI) | Σ R | Max DD (R) | Náhodné Ø R | Výhoda |
|---|---|---|---|---|---|---|---|
| BTC/USDT | 119 | 38.7 | -0.074 ± 0.264 | -8.8 | 14.76 | -0.253 | +0.179 |
| ETH/USDT | 117 | 39.3 | +0.103 ± 0.327 | +12.0 | 17.93 | -0.235 | +0.338 |
| SOL/USDT | 144 | 37.5 | +0.147 ± 0.315 | +21.1 | 15.96 | -0.161 | +0.308 |
| XRP/USDT | 112 | 37.5 | +0.044 ± 0.318 | +4.9 | 17.66 | -0.132 | +0.176 |
| ADA/USDT | 115 | 34.8 | +0.002 ± 0.341 | +0.2 | 20.4 | -0.104 | +0.106 |
| LINK/USDT | 99 | 38.4 | +0.137 ± 0.388 | +13.6 | 13.66 | -0.157 | +0.294 |
| AVAX/USDT | 117 | 33.3 | +0.195 ± 0.393 | +22.9 | 23.23 | -0.112 | +0.307 |
| DOGE/USDT | 127 | 27.6 | -0.072 ± 0.336 | -9.2 | 28.8 | -0.085 | +0.013 |
| **celkem** | 950 | 35.8 | +0.060 ± 0.119 | +56.7 | 98.88 | -0.155 | +0.215 |
| in-sample 70 % | 698 | 35.7 | +0.091 ± 0.142 | +63.5 | 69.72 | -0.103 | +0.194 |
| out-of-sample 30 % | 252 | 36.1 | -0.027 ± 0.210 | -6.8 | 52.83 | -0.236 | +0.209 |

## Strategie (celá historie, in-sample 70 % / out-of-sample 30 %)

| Strategie | Obchody | Ø R celkem | IS Ø R | OOS Ø R (95% CI) | Náhodné (OOS) |
|---|---|---|---|---|---|
| donchian_1d | 625 | +0.393 | +0.497 | +0.152 ± 0.207 | +0.057 |
| pullback_1d | 645 | +0.288 | +0.380 | +0.151 ± 0.207 | +0.023 |

