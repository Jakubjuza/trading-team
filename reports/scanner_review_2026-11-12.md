# Vyhodnocení skeneru 2026-11-12 08:10 UTC

Náklady: poplatek 0.1 % + skluz 0.05 % na stranu (≈ 0.30 % ceny za celý obchod). Výsledky v R po nákladech.

## Odeslané signály (6)

- BTC/USDT 1h short 2026-10-24T16:00 (stop 0.21 %): stop, -2.44 R za 2 svíček
- ETH/USDT 1d short 2026-10-29T00:00 (stop 8.03 %): stop, -1.04 R za 6 svíček
- SOL/USDT 1d short 2026-10-29T00:00 (stop 8.68 %): open, +1.50 R za 14 svíček
- XRP/USDT 1d short 2026-10-29T00:00 (stop 13.56 %): open, +1.14 R za 14 svíček
- DOGE/USDT 1d short 2026-10-29T00:00 (stop 8.48 %): open, +1.28 R za 14 svíček
- SOL/USDT 1d short 2026-11-05T00:00 (stop 10.49 %): open, +0.66 R za 7 svíček

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
| BTC/USDT | 116 | 38.8 | -0.071 ± 0.269 | -8.3 | 14.76 | -0.320 | +0.249 |
| ETH/USDT | 117 | 39.3 | +0.081 ± 0.323 | +9.5 | 17.93 | -0.237 | +0.318 |
| SOL/USDT | 140 | 37.9 | +0.151 ± 0.318 | +21.2 | 15.96 | -0.171 | +0.322 |
| XRP/USDT | 114 | 36.8 | +0.022 ± 0.314 | +2.5 | 16.46 | -0.113 | +0.135 |
| ADA/USDT | 115 | 34.8 | +0.002 ± 0.341 | +0.2 | 20.39 | -0.159 | +0.161 |
| LINK/USDT | 98 | 37.8 | +0.095 ± 0.382 | +9.3 | 13.66 | -0.164 | +0.259 |
| AVAX/USDT | 115 | 33.9 | +0.220 ± 0.399 | +25.2 | 23.23 | -0.165 | +0.385 |
| DOGE/USDT | 125 | 28.0 | -0.054 ± 0.341 | -6.8 | 28.8 | -0.125 | +0.071 |
| **celkem** | 940 | 35.9 | +0.056 ± 0.119 | +52.8 | 98.88 | -0.181 | +0.237 |
| in-sample 70 % | 700 | 35.0 | +0.062 ± 0.141 | +43.2 | 69.72 | -0.111 | +0.173 |
| out-of-sample 30 % | 240 | 38.3 | +0.040 ± 0.219 | +9.6 | 32.94 | -0.223 | +0.263 |

## Strategie (celá historie, in-sample 70 % / out-of-sample 30 %)

| Strategie | Obchody | Ø R celkem | IS Ø R | OOS Ø R (95% CI) | Náhodné (OOS) |
|---|---|---|---|---|---|
| donchian_1d | 627 | +0.393 | +0.503 | +0.083 ± 0.200 | +0.028 |
| pullback_1d | 648 | +0.296 | +0.381 | +0.120 ± 0.197 | +0.062 |

## Hypotéza H3 – `skip_weekends: true` (research/knowledge.md)

Předem stanoveno: vynechat setupy s hold svíčkou v so/ne (UTC) zvlášť pro donchian_1d a pullback_1d, nic jiného se nemění. Stejná metodika jako tabulka „Strategie“ (8 mincí, IS/OOS 70/30, náhodné vstupy, náklady z configu).

| Strategie | Varianta | IS n | IS Ø R | OOS n | OOS Ø R (95% CI) | Náhodné (OOS) | OOS 1. pol. | OOS 2. pol. | Mince lepší (OOS) |
|---|---|---|---|---|---|---|---|---|---|
| donchian_1d | dnes | 458 | +0.503 | 171 | +0.083 ± 0.200 | +0.028 | −0.032 | +0.227 | |
| donchian_1d | skip_weekends | 401 | +0.486 | 148 | +0.181 ± 0.216 | +0.049 | +0.130 | +0.239 | 7/8 |
| pullback_1d | dnes | 428 | +0.381 | 222 | +0.120 ± 0.197 | +0.062 | +0.155 | +0.125 | |
| pullback_1d | skip_weekends | 386 | +0.360 | 198 | +0.188 ± 0.196 | +0.065 | +0.163 | +0.222 | 6/8 |

Výsledek: kritérium hypotézy (OOS ≥ +0,05 R, ≥ 100 OOS obchodů, nad náhodou) splněno u obou, ale brána změny configu ne – in-sample se zhoršil (−0,017 / −0,021 R) a rozdíly jsou hluboko v intervalu spolehlivosti. **Neprošla → config beze změny.** Přepnutí je ano/ne, žádné sousední hodnoty se netestovaly.

## Závěr kontroly

- Obě zapnuté strategie mají OOS Ø R > 0 a porážejí náhodné vstupy (donchian +0,055 R, pullback +0,058 R nad náhodou) → nevypínat. OOS je výrazně slabší než IS (pokles z +0,50/+0,38 na +0,08/+0,12 R) a CI zahrnuje nulu.
- Skutečné uzavřené obchody: 2 signály (−3,48 R), v research/outcomes.jsonl 4 uzavřené papírové obchody vč. MTF (Σ −4,51 R) – vzorek je zatím příliš malý na závěr.
- Desk: 0 uzavřených A/B, 2 zamítnuté (C/NO_TRADE) skončily −1,74 R průměrně → zamítnutí zatím sedí, ale n = 2.
- Kalibrace scénářů (neutrální střed, 2022–2026): pod medvědím 10–12 %, nad mediánem 45–46 %, nad býčím 6–7 % – v pásmu ~10/50/10, býčí okraj mírně široký.
