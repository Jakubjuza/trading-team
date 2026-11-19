# Vyhodnocení skeneru 2026-11-19 08:09 UTC

Náklady: poplatek 0.1 % + skluz 0.05 % na stranu (≈ 0.30 % ceny za celý obchod). Výsledky v R po nákladech.

## Odeslané signály (6)

- BTC/USDT 1h short 2026-10-24T16:00 (stop 0.21 %): stop, -2.44 R za 2 svíček
- ETH/USDT 1d short 2026-10-29T00:00 (stop 8.03 %): stop, -1.04 R za 6 svíček
- SOL/USDT 1d short 2026-10-29T00:00 (stop 8.68 %): time, +2.29 R za 20 svíček
- XRP/USDT 1d short 2026-10-29T00:00 (stop 13.56 %): time, +1.78 R za 20 svíček
- DOGE/USDT 1d short 2026-10-29T00:00 (stop 8.48 %): time, +2.27 R za 20 svíček
- SOL/USDT 1d short 2026-11-05T00:00 (stop 10.49 %): open, +1.76 R za 14 svíček

Uzavřené: {'n': 5, 'win': 60.0, 'avg_r': 0.573, 'ci': 1.909, 'sum_r': 2.86, 'max_dd_r': 1.04}

## Verdikty desku vs. výsledek

| Skupina | Uzavřené obchody | Win % | Ø R | Σ R |
|---|---|---|---|---|
| schváleno (A/B) | 0 | 0.0 | +0.000 | +0.00 |
| zamítnuto (C/NO_TRADE) | 5 | 60.0 | +0.573 | +2.86 |
| bez verdiktu | 0 | 0.0 | +0.000 | +0.00 |

Desk přidává hodnotu, jen když „schváleno (A/B)“ dlouhodobě vychází lépe než „zamítnuto“.

## Backtest aktuálního nastavení (BTC/USDT 17291 svíček, ETH/USDT 17289 svíček, SOL/USDT 17291 svíček, XRP/USDT 17291 svíček, ADA/USDT 17289 svíček, LINK/USDT 17289 svíček, AVAX/USDT 17291 svíček, DOGE/USDT 17291 svíček)

| | Obchody | Win % | Ø R (95% CI) | Σ R | Max DD (R) | Náhodné Ø R | Výhoda |
|---|---|---|---|---|---|---|---|
| BTC/USDT | 108 | 40.7 | -0.015 ± 0.287 | -1.6 | 12.92 | -0.259 | +0.244 |
| ETH/USDT | 114 | 38.6 | +0.113 ± 0.332 | +12.9 | 15.57 | -0.204 | +0.317 |
| SOL/USDT | 140 | 37.9 | +0.150 ± 0.317 | +20.9 | 16.05 | -0.070 | +0.220 |
| XRP/USDT | 110 | 36.4 | +0.015 ± 0.319 | +1.6 | 15.26 | -0.151 | +0.166 |
| ADA/USDT | 111 | 34.2 | -0.024 ± 0.347 | -2.7 | 19.46 | -0.139 | +0.115 |
| LINK/USDT | 97 | 39.2 | +0.121 ± 0.384 | +11.7 | 11.7 | -0.179 | +0.300 |
| AVAX/USDT | 111 | 35.1 | +0.255 ± 0.407 | +28.2 | 21.46 | -0.125 | +0.380 |
| DOGE/USDT | 122 | 30.3 | +0.035 ± 0.353 | +4.2 | 22.21 | -0.134 | +0.169 |
| **celkem** | 913 | 36.5 | +0.082 ± 0.122 | +75.3 | 77.84 | -0.154 | +0.236 |
| in-sample 70 % | 685 | 35.8 | +0.086 ± 0.143 | +58.6 | 53.77 | -0.120 | +0.206 |
| out-of-sample 30 % | 228 | 38.6 | +0.073 ± 0.229 | +16.7 | 26.32 | -0.218 | +0.291 |

## Strategie (celá historie, in-sample 70 % / out-of-sample 30 %)

| Strategie | Obchody | Ø R celkem | IS Ø R | OOS Ø R (95% CI) | Náhodné (OOS) |
|---|---|---|---|---|---|
| donchian_1d | 632 | +0.393 | +0.481 | +0.153 ± 0.205 | +0.049 |
| pullback_1d | 648 | +0.296 | +0.385 | +0.131 ± 0.199 | +0.067 |

## Hypotéza H3 – `skip_weekends: true` (zvlášť pro každou strategii, jiné parametry beze změny)

Metodika jako tabulka „Strategie“: denní data 8 mincí, IS/OOS 70/30, náhodné vstupy se stejnými stopy/cíli, náklady 0,15 % na stranu.

| Strategie | Varianta | IS n | IS Ø R | OOS n | OOS Ø R (95% CI) | Náhodné OOS | OOS 1. pol. | OOS 2. pol. | Mince OOS lepší |
|---|---|---|---|---|---|---|---|---|---|
| donchian_1d | aktuální (false) | 463 | +0.481 | 169 | +0.153 ± 0.205 | +0.049 | +0.071 (n 94) | +0.251 (n 79) | – |
| donchian_1d | skip_weekends | 405 | +0.466 | 147 | +0.255 ± 0.220 | +0.051 | +0.259 (n 77) | +0.265 (n 73) | 8/8 |
| pullback_1d | aktuální (false) | 429 | +0.385 | 220 | +0.131 ± 0.199 | +0.067 | +0.200 (n 93) | +0.080 (n 127) | – |
| pullback_1d | skip_weekends | 387 | +0.364 | 197 | +0.194 ± 0.197 | +0.056 | +0.222 (n 85) | +0.173 (n 112) | 7/8 |

Kritérium hypotézy (OOS +≥ 0,05 R, ≥ 100 OOS obchodů, nad náhodou) splněno u obou (+0,102 / +0,063 R), ale pravidlo
pro změnu configu „in-sample není horší“ splněno není: IS −0,015 R (Donchian) a −0,021 R (pullback). Zlepšení je
v rámci šumu (CI ± 0,2 R) a omezené na poslední období – stejně jako u vlastního pohledu z 25. 10. (za 10 let bez rozdílu).
**Výsledek: neprošla – beze změny configu.**
