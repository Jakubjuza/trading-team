# Vyhodnocení skeneru 2026-10-29 08:16 UTC

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
| BTC/USDT | 120 | 38.3 | -0.083 ± 0.262 | -10.0 | 14.76 | -0.220 | +0.137 |
| ETH/USDT | 115 | 39.1 | +0.105 ± 0.332 | +12.1 | 17.93 | -0.220 | +0.325 |
| SOL/USDT | 143 | 37.1 | +0.117 ± 0.312 | +16.8 | 15.96 | -0.146 | +0.263 |
| XRP/USDT | 111 | 37.8 | +0.055 ± 0.320 | +6.2 | 17.66 | -0.154 | +0.209 |
| ADA/USDT | 114 | 34.2 | -0.007 ± 0.344 | -0.8 | 20.4 | -0.105 | +0.098 |
| LINK/USDT | 99 | 38.4 | +0.137 ± 0.388 | +13.6 | 13.66 | -0.170 | +0.307 |
| AVAX/USDT | 116 | 33.6 | +0.207 ± 0.396 | +24.1 | 23.23 | -0.122 | +0.329 |
| DOGE/USDT | 127 | 27.6 | -0.072 ± 0.336 | -9.2 | 28.8 | -0.084 | +0.012 |
| **celkem** | 945 | 35.7 | +0.056 ± 0.119 | +52.7 | 98.88 | -0.152 | +0.208 |
| in-sample 70 % | 689 | 35.3 | +0.075 ± 0.143 | +51.4 | 69.72 | -0.143 | +0.218 |
| out-of-sample 30 % | 256 | 36.7 | +0.005 ± 0.211 | +1.3 | 55.23 | -0.228 | +0.233 |

## Strategie (celá historie, in-sample 70 % / out-of-sample 30 %)

| Strategie | Obchody | Ø R celkem | IS Ø R | OOS Ø R (95% CI) | Náhodné (OOS) |
|---|---|---|---|---|---|
| donchian_1d | 625 | +0.389 | +0.487 | +0.160 ± 0.207 | +0.068 |
| pullback_1d | 645 | +0.288 | +0.372 | +0.135 ± 0.200 | +0.033 |


## H3 – `skip_weekends` u denních strategií (29. 10. 2026, neprošla)

| Strategie | skip_weekends | IS Ø R | OOS n | OOS Ø R ± CI | náhoda OOS | 1. půle OOS | 2. půle OOS |
|---|---|---|---|---|---|---|---|
| donchian_1d | false | +0,487 | 171 | +0,160 ± 0,207 | +0,068 | +0,087 | +0,258 |
| donchian_1d | true | +0,470 | 148 | +0,239 ± 0,224 | +0,057 | +0,211 | +0,273 |
| pullback_1d | false | +0,372 | 220 | +0,135 ± 0,200 | +0,033 | +0,227 | +0,073 |
| pullback_1d | true | +0,354 | 197 | +0,184 ± 0,198 | +0,062 | +0,279 | +0,118 |

Lepší OOS Ø R na 6/8 mincí u obou. Kritéria nesplněna: IS není horší (u obou je horší), pullback zlepšení +0,049 < 0,05 R.
