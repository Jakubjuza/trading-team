# Vyhodnocení skeneru 2026-11-09 08:16 UTC

Náklady: poplatek 0.1 % + skluz 0.05 % na stranu (≈ 0.30 % ceny za celý obchod). Výsledky v R po nákladech.

## Odeslané signály (6)

- BTC/USDT 1h short 2026-10-24T16:00 (stop 0.21 %): stop, -2.44 R za 2 svíček
- ETH/USDT 1d short 2026-10-29T00:00 (stop 8.03 %): stop, -1.04 R za 6 svíček
- SOL/USDT 1d short 2026-10-29T00:00 (stop 8.68 %): open, +1.15 R za 11 svíček
- XRP/USDT 1d short 2026-10-29T00:00 (stop 13.56 %): open, +0.89 R za 11 svíček
- DOGE/USDT 1d short 2026-10-29T00:00 (stop 8.48 %): open, +1.05 R za 11 svíček
- SOL/USDT 1d short 2026-11-05T00:00 (stop 10.49 %): open, +0.35 R za 4 svíček

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
| BTC/USDT | 118 | 38.1 | -0.090 ± 0.266 | -10.6 | 14.76 | -0.304 | +0.214 |
| ETH/USDT | 116 | 39.7 | +0.092 ± 0.325 | +10.7 | 17.93 | -0.184 | +0.276 |
| SOL/USDT | 140 | 37.1 | +0.136 ± 0.318 | +19.0 | 15.96 | -0.176 | +0.312 |
| XRP/USDT | 113 | 37.2 | +0.033 ± 0.316 | +3.7 | 16.46 | -0.157 | +0.190 |
| ADA/USDT | 115 | 34.8 | +0.002 ± 0.341 | +0.2 | 20.39 | -0.116 | +0.118 |
| LINK/USDT | 97 | 38.1 | +0.108 ± 0.386 | +10.5 | 13.66 | -0.216 | +0.324 |
| AVAX/USDT | 115 | 33.9 | +0.220 ± 0.399 | +25.2 | 23.23 | -0.127 | +0.347 |
| DOGE/USDT | 125 | 28.0 | -0.054 ± 0.341 | -6.8 | 28.8 | -0.118 | +0.064 |
| **celkem** | 939 | 35.8 | +0.055 ± 0.119 | +51.9 | 98.88 | -0.174 | +0.229 |
| in-sample 70 % | 693 | 35.2 | +0.072 ± 0.142 | +50.0 | 69.72 | -0.140 | +0.212 |
| out-of-sample 30 % | 246 | 37.4 | +0.008 ± 0.215 | +1.9 | 43.27 | -0.272 | +0.280 |

## Strategie (celá historie, in-sample 70 % / out-of-sample 30 %)

| Strategie | Obchody | Ø R celkem | IS Ø R | OOS Ø R (95% CI) | Náhodné (OOS) |
|---|---|---|---|---|---|
| donchian_1d | 626 | +0.393 | +0.500 | +0.124 ± 0.207 | +0.038 |
| pullback_1d | 645 | +0.288 | +0.381 | +0.121 ± 0.199 | +0.024 |


## Hypotéza H3 – `skip_weekends` (9. 11. 2026, předem stanovená)

| Strategie | Varianta | IS Ø R | OOS n | OOS Ø R ± CI | Náhodné (OOS) | OOS 1. / 2. polovina |
|---|---|---|---|---|---|---|
| donchian_1d | bez filtru | +0,500 | 171 | +0,124 ± 0,207 | +0,038 | +0,046 / +0,223 |
| donchian_1d | skip_weekends | +0,483 | 148 | +0,229 ± 0,225 | +0,044 | +0,223 / +0,235 |
| pullback_1d | bez filtru | +0,381 | 220 | +0,121 ± 0,199 | +0,024 | +0,182 / +0,091 |
| pullback_1d | skip_weekends | +0,360 | 197 | +0,183 ± 0,198 | +0,041 | +0,263 / +0,140 |

Zlepšení OOS +0,105 / +0,062 R, ale in-sample je u obou o 0,02 R horší a rozdíl je v rámci intervalů spolehlivosti → podmínka „IS není horší“ nesplněna, **config beze změny**.
Poznámka: scanner/config.yaml nyní nemá `skip_weekends` v `params` denních strategií (jen ve vypnuté brh_1h).
