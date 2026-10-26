# Vyhodnocení skeneru 2026-10-26 08:16 UTC

Náklady: poplatek 0.1 % + skluz 0.05 % na stranu (≈ 0.30 % ceny za celý obchod). Výsledky v R po nákladech.

## Odeslané signály (1)

- BTC/USDT 1h short 2026-10-24T16:00 (stop 0.21 %): stop, -2.44 R za 2 svíček

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
| BTC/USDT | 121 | 38.0 | -0.092 ± 0.261 | -11.2 | 14.76 | -0.315 | +0.223 |
| ETH/USDT | 117 | 38.5 | +0.083 ± 0.328 | +9.7 | 17.93 | -0.284 | +0.367 |
| SOL/USDT | 144 | 36.8 | +0.108 ± 0.311 | +15.6 | 15.96 | -0.173 | +0.281 |
| XRP/USDT | 112 | 37.5 | +0.044 ± 0.318 | +4.9 | 17.66 | -0.160 | +0.204 |
| ADA/USDT | 115 | 33.9 | -0.017 ± 0.341 | -2.0 | 20.4 | -0.173 | +0.156 |
| LINK/USDT | 100 | 40.0 | +0.186 ± 0.387 | +18.6 | 13.66 | -0.188 | +0.374 |
| AVAX/USDT | 118 | 33.1 | +0.186 ± 0.390 | +21.9 | 23.23 | -0.145 | +0.331 |
| DOGE/USDT | 126 | 27.8 | -0.063 ± 0.338 | -8.0 | 28.8 | -0.094 | +0.031 |
| **celkem** | 953 | 35.6 | +0.052 ± 0.118 | +49.6 | 98.88 | -0.191 | +0.243 |
| in-sample 70 % | 698 | 35.1 | +0.067 ± 0.141 | +47.1 | 69.72 | -0.118 | +0.185 |
| out-of-sample 30 % | 255 | 36.9 | +0.010 ± 0.212 | +2.5 | 55.23 | -0.192 | +0.202 |

## Strategie (celá historie, in-sample 70 % / out-of-sample 30 %)

| Strategie | Obchody | Ø R celkem | IS Ø R | OOS Ø R (95% CI) | Náhodné (OOS) |
|---|---|---|---|---|---|
| donchian_1d | 623 | +0.393 | +0.493 | +0.180 ± 0.208 | +0.062 |
| pullback_1d | 645 | +0.288 | +0.372 | +0.145 ± 0.200 | +0.043 |


## Hypotéza H3 – skip_weekends u denních strategií (26. 10. 2026)

Metodika: IS/OOS 70/30, náklady z configu (0,15 % na stranu), náhodné vstupy, jiné parametry beze změny.

| Strategie | Varianta | IS Ø R | OOS n | OOS Ø R (CI) | Náhoda OOS | OOS 1. / 2. polovina |
|---|---|---|---|---|---|---|
| donchian_1d | všechny dny | +0,493 | 171 | +0,180 ± 0,208 | +0,062 | +0,105 / +0,323 |
| donchian_1d | skip_weekends | +0,479 | 148 | +0,239 ± 0,224 | +0,056 | +0,191 / +0,344 |
| pullback_1d | všechny dny | +0,372 | 220 | +0,145 ± 0,200 | +0,043 | +0,251 / +0,056 |
| pullback_1d | skip_weekends | +0,354 | 197 | +0,195 ± 0,198 | +0,060 | +0,305 / +0,108 |

Výsledek: **neprošla** – in-sample je u obou horší (−0,014 / −0,018 R), pullback jen na hraně +0,05 R. Beze změny configu.
