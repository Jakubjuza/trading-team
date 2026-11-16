# Vyhodnocení skeneru 2026-11-16 08:14 UTC

Náklady: poplatek 0.1 % + skluz 0.05 % na stranu (≈ 0.30 % ceny za celý obchod). Výsledky v R po nákladech.

## Odeslané signály (6)

- BTC/USDT 1h short 2026-10-24T16:00 (stop 0.21 %): stop, -2.44 R za 2 svíček
- ETH/USDT 1d short 2026-10-29T00:00 (stop 8.03 %): stop, -1.04 R za 6 svíček
- SOL/USDT 1d short 2026-10-29T00:00 (stop 8.68 %): open, +2.46 R za 18 svíček
- XRP/USDT 1d short 2026-10-29T00:00 (stop 13.56 %): open, +1.82 R za 18 svíček
- DOGE/USDT 1d short 2026-10-29T00:00 (stop 8.48 %): open, +2.28 R za 18 svíček
- SOL/USDT 1d short 2026-11-05T00:00 (stop 10.49 %): open, +1.96 R za 11 svíček

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
| BTC/USDT | 116 | 39.7 | -0.035 ± 0.273 | -4.1 | 14.76 | -0.258 | +0.223 |
| ETH/USDT | 117 | 40.2 | +0.125 ± 0.329 | +14.7 | 17.93 | -0.204 | +0.329 |
| SOL/USDT | 142 | 38.0 | +0.147 ± 0.314 | +20.8 | 15.96 | -0.192 | +0.339 |
| XRP/USDT | 114 | 36.8 | +0.022 ± 0.314 | +2.5 | 16.46 | -0.193 | +0.215 |
| ADA/USDT | 115 | 34.8 | +0.001 ± 0.341 | +0.2 | 20.39 | -0.145 | +0.146 |
| LINK/USDT | 99 | 38.4 | +0.103 ± 0.379 | +10.2 | 13.66 | -0.148 | +0.251 |
| AVAX/USDT | 116 | 34.5 | +0.228 ± 0.396 | +26.4 | 23.23 | -0.164 | +0.392 |
| DOGE/USDT | 126 | 28.6 | -0.020 ± 0.345 | -2.5 | 28.8 | -0.148 | +0.128 |
| **celkem** | 945 | 36.3 | +0.072 ± 0.119 | +68.2 | 98.88 | -0.182 | +0.254 |
| in-sample 70 % | 702 | 34.9 | +0.058 ± 0.140 | +40.8 | 69.72 | -0.139 | +0.197 |
| out-of-sample 30 % | 243 | 40.3 | +0.113 ± 0.222 | +27.4 | 29.96 | -0.254 | +0.367 |

## Strategie (celá historie, in-sample 70 % / out-of-sample 30 %)

| Strategie | Obchody | Ø R celkem | IS Ø R | OOS Ø R (95% CI) | Náhodné (OOS) |
|---|---|---|---|---|---|
| donchian_1d | 628 | +0.387 | +0.488 | +0.096 ± 0.202 | +0.060 |
| pullback_1d | 648 | +0.296 | +0.385 | +0.131 ± 0.199 | +0.077 |

## Uzavřené papírové obchody (research/outcomes.jsonl)

4 uzavřené, všechny shorty z 29. 10. 2026 na stopu: ETH donchian_1d −1,04 R, ETH donchian_1d+mtf −1,20 R, XRP pullback_1d+mtf −1,13 R, DOGE pullback_1d+mtf −1,14 R → Σ −4,51 R, Ø −1,13 R. Otevřené shorty (SOL, XRP, DOGE z 29. 10., SOL z 5. 11.) jsou v zisku +1,8 až +2,5 R. Vzorek je příliš malý na závěr.

## Hypotéza H3 – bez víkendových vstupů (`skip_weekends: true`), předem stanovená

Stejná metodika jako tabulka „Strategie“ (IS/OOS 70/30, náhodné vstupy, náklady z configu); jiné parametry beze změny. Poloviny OOS = OOS rozsah každé mince rozdělený napůl.

| Strategie | Varianta | IS n | IS Ø R | OOS n | OOS Ø R (95% CI) | Náhodné OOS | OOS 1. pol. | OOS 2. pol. | Mince lepší |
|---|---|---|---|---|---|---|---|---|---|
| donchian_1d | dnes | 461 | +0.488 | 169 | +0.096 ± 0.202 | +0.060 | +0.060 (n=95) | +0.175 (n=76) | |
| donchian_1d | skip_weekends | 403 | +0.473 | 147 | +0.190 ± 0.217 | +0.077 | +0.226 (n=79) | +0.182 (n=70) | 8/8 |
| pullback_1d | dnes | 429 | +0.385 | 220 | +0.131 ± 0.199 | +0.077 | +0.181 (n=92) | +0.111 (n=129) | |
| pullback_1d | skip_weekends | 387 | +0.364 | 197 | +0.194 ± 0.197 | +0.062 | +0.177 (n=83) | +0.206 (n=114) | 6/8 |

Kritéria (OOS ≥ 100, OOS zlepšení ≥ 0,05 R, nad náhodou, IS ne horší, drží v obou polovinách OOS a na většině mincí):
- donchian_1d: OOS +0,094 R ✅, n 147 ✅, nad náhodou ✅, mince 8/8 ✅, **IS horší (−0,015) ❌**, 2. polovina OOS jen +0,007 (prakticky beze změny) ❌.
- pullback_1d: OOS +0,063 R ✅, n 197 ✅, nad náhodou ✅, mince 6/8 ✅, **IS horší (−0,021) ❌**, 1. polovina OOS −0,004 ❌.

**Výsledek: H3 neprošla** – zlepšení jen v OOS, ne v IS ani v obou polovinách OOS; rozdíly jsou hluboko uvnitř CI (±0,2 R). Config beze změny.

## Závěr

- Obě zapnuté strategie mají OOS Ø R > 0 a porážejí náhodné vstupy (donchian_1d +0,096 vs. +0,060, výhoda +0,036; pullback_1d +0,131 vs. +0,077, výhoda +0,054) → žádné vypnutí. CI ±0,2 R je ale širší než výhoda.
- IS (+0,49 / +0,39) je výrazně nad OOS (+0,10 / +0,13) – pokles výkonu v posledních letech trvá (viz reports/adaptive.md).
- Desk: 0 uzavřených obchodů A/B, 2 zamítnuté (C/NO_TRADE) Ø −1,74 R → zatím nelze hodnotit (H12 čeká na ≥ 50).
- Kalibrace scénářů (neutrální střed, roky 2022–2026): pod medvědím 10–12 %, nad mediánem 45–46 %, nad býčím 6–7 %, v pásmu 81–83 % → v pásmu; býčí okraj mírně příliš široký.
- Beze změny configu.
