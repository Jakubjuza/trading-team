# Atlas strategií – 15 rodin, 7 timeframů, poplatky MEXC (27. 10. 2026)

Otázka: je mezi běžnými pravidlovými strategiemi na kterémkoli timeframu něco, co po poplatcích MEXC vydělává spolehlivěji než náhoda? Metoda stanovená předem je v hlavičce `research/experiments/strategy_atlas.py`.

- **42 048 kombinací** (15 rodin, 248 variant × 7 timeframů × 3 filtry × 4 výstupy × long/short), 8 mincí.
- 12h: 5952 kombinací, 1259 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 15m: 5952 kombinací, 4464 s, data od BTC 01/2022, ETH 01/2022, SOL 01/2022, XRP 01/2022, ADA 01/2022, LINK 01/2022, AVAX 01/2022, DOGE 01/2022
- 1d: 5952 kombinací, 1225 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 1h: 5952 kombinací, 871 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 2h: 5952 kombinací, 856 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 4h: 5952 kombinací, 749 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 6h: 5952 kombinací, 844 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- sent_1d: 192 kombinací, 985 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- sent_4h: 192 kombinací, 2 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- Poplatky na stranu: **MEXC futures taker 0,02 % + skluz 0,03 % = 0,05 % (rozhoduje)**; MEXC spot taker 0,08 %; maker 0 % (optimistická mez); 0,15 % (dřívější testy). Funding nezapočten. Poplatky MEXC podle [MEXC, 11/2025](https://www.mexc.com/ru-RU/crypto-pulse/article/mexc-trading-fees-complete-guide-39643).
- IS do 12/2023 (15M od 1/2022), OOS 1/2024–6/2025, HOLDOUT 7/2025–dnes. R = výsledek po poplatcích / riziko (vzdálenost stopu; bez stopu 2 ATR).

## 1. Mají rodiny strategií výhodu? (hlavní scénář poplatků)

„Nad náhodou“ = podíl kombinací, jejichž Ø R v daném období je nad mediánem jejich vlastních náhodných vstupů (bez výhody by to bylo ~50 %). „Obě nad p95“ = OOS i HOLDOUT nad 95. percentilem náhody (čistou náhodou ~0,25 %).

| Rodina | Směr | Kombinací | OOS > 0 | HOLDOUT > 0 | OOS nad náhodou | HOLDOUT nad náhodou | Obě nad p95 | Medián OOS R | Medián HOLDOUT R |
|---|---|---|---|---|---|---|---|---|---|
| Bollinger průraz | long | 336 | 81% | 76% | 93% | 89% | 49,1% | +0,25 | +0,18 |
| Bollinger průraz | short | 336 | 32% | 72% | 52% | 84% | 13,1% | -0,06 | +0,08 |
| Bollinger návrat | long | 336 | 21% | 30% | 17% | 32% | 0,0% | -0,11 | -0,07 |
| Bollinger návrat | short | 336 | 33% | 50% | 45% | 44% | 4,5% | -0,05 | +0,00 |
| svíčkové vzory | long | 168 | 50% | 44% | 62% | 46% | 0,0% | -0,00 | -0,01 |
| svíčkové vzory | short | 168 | 23% | 58% | 62% | 51% | 2,4% | -0,06 | +0,03 |
| Donchian průraz | long | 420 | 80% | 64% | 95% | 83% | 31,7% | +0,25 | +0,09 |
| Donchian průraz | short | 420 | 30% | 64% | 49% | 51% | 2,1% | -0,08 | +0,04 |
| strach a chamtivost | long | 192 | 35% | 25% | 28% | 23% | 0,5% | -0,16 | -0,29 |
| strach a chamtivost | short | 192 | 41% | 15% | 50% | 18% | 1,6% | +0,04 | -0,23 |
| Keltner průraz | long | 252 | 80% | 69% | 96% | 88% | 47,6% | +0,19 | +0,14 |
| Keltner průraz | short | 252 | 40% | 64% | 56% | 76% | 17,5% | -0,05 | +0,06 |
| protnutí 2 průměrů | long | 16128 | 66% | 55% | 70% | 64% | 8,2% | +0,16 | +0,03 |
| protnutí 2 průměrů | short | 16128 | 31% | 65% | 69% | 54% | 5,5% | -0,07 | +0,07 |
| MACD | long | 504 | 63% | 56% | 75% | 54% | 8,3% | +0,10 | +0,03 |
| MACD | short | 504 | 45% | 57% | 80% | 50% | 8,9% | -0,01 | +0,01 |
| cena × průměr | long | 840 | 54% | 55% | 55% | 46% | 5,1% | +0,02 | +0,02 |
| cena × průměr | short | 840 | 37% | 60% | 88% | 51% | 12,9% | -0,02 | +0,02 |
| momentum ROC | long | 336 | 56% | 51% | 54% | 51% | 4,2% | +0,02 | +0,00 |
| momentum ROC | short | 336 | 32% | 56% | 81% | 42% | 8,0% | -0,04 | +0,01 |
| RSI momentum | long | 252 | 62% | 62% | 73% | 67% | 13,1% | +0,06 | +0,04 |
| RSI momentum | short | 252 | 37% | 67% | 87% | 62% | 12,3% | -0,02 | +0,03 |
| RSI návrat | long | 336 | 23% | 20% | 24% | 24% | 0,0% | -0,09 | -0,09 |
| RSI návrat | short | 336 | 24% | 46% | 35% | 45% | 6,5% | -0,07 | -0,01 |
| Stochastic | long | 168 | 22% | 24% | 18% | 23% | 0,0% | -0,11 | -0,07 |
| Stochastic | short | 168 | 11% | 57% | 27% | 62% | 2,4% | -0,07 | +0,01 |
| Supertrend | long | 252 | 67% | 57% | 81% | 56% | 2,8% | +0,14 | +0,02 |
| Supertrend | short | 252 | 55% | 67% | 79% | 60% | 6,0% | +0,02 | +0,06 |
| sweep & reclaim | long | 168 | 34% | 14% | 19% | 13% | 0,0% | -0,10 | -0,11 |
| sweep & reclaim | short | 168 | 12% | 60% | 23% | 49% | 0,6% | -0,11 | +0,03 |
| průraz s objemem | long | 336 | 80% | 69% | 96% | 83% | 38,1% | +0,36 | +0,19 |
| průraz s objemem | short | 336 | 27% | 61% | 41% | 57% | 6,2% | -0,14 | +0,06 |

## 2. Podle timeframu (všechny rodiny dohromady)

| TF | Směr | OOS > 0 | HOLDOUT > 0 | OOS nad náhodou | HOLDOUT nad náhodou | Medián OOS R | Medián obchodů/měs. |
|---|---|---|---|---|---|---|---|
| 15m | long | 22% | 27% | 81% | 61% | -0,08 | 147 |
| 15m | short | 32% | 2% | 88% | 53% | -0,03 | 202 |
| 1h | long | 61% | 64% | 76% | 53% | +0,05 | 40 |
| 1h | short | 54% | 40% | 72% | 45% | +0,01 | 44 |
| 2h | long | 69% | 63% | 72% | 58% | +0,10 | 20 |
| 2h | short | 41% | 64% | 62% | 41% | -0,02 | 22 |
| 4h | long | 75% | 66% | 70% | 59% | +0,17 | 10 |
| 4h | short | 32% | 76% | 67% | 41% | -0,07 | 11 |
| 6h | long | 77% | 61% | 61% | 63% | +0,44 | 7 |
| 6h | short | 28% | 84% | 71% | 60% | -0,10 | 8 |
| 12h | long | 76% | 59% | 62% | 76% | +0,48 | 4 |
| 12h | short | 22% | 87% | 65% | 65% | -0,18 | 4 |
| 1d | long | 65% | 38% | 58% | 63% | +0,30 | 2 |
| 1d | short | 12% | 86% | 51% | 73% | -0,28 | 2 |

## 3. Kolik dělají poplatky

Podíl všech kombinací s kladným Ø R v OOS a v HOLDOUT podle výše poplatků:

| Poplatky na stranu | OOS > 0 long | OOS > 0 short | HOLDOUT > 0 long | HOLDOUT > 0 short | Projde pravidlem (ze všech) |
|---|---|---|---|---|---|
| 0 % (maker, optimisticky) | 76% | 47% | 66% | 86% | 1006 z 33868 |
| 0,05 % (MEXC futures taker) | 64% | 31% | 54% | 63% | 197 z 33868 |
| 0,08 % (MEXC spot taker) | 60% | 23% | 49% | 56% | 131 z 33868 |
| 0,15 % (dřívější testy) | 54% | 14% | 40% | 48% | 62 z 33868 |

## 4. Výběr podle předem stanoveného pravidla (50 nejlepších podle IS t-statistiky na směr)

| Směr | Kombinace | IS n / Ø R | OOS n / Ø R | OOS t | Náhoda OOS p95 | HOLDOUT n / Ø R | Náhoda HOLD p95 | Max. propad R | Obch./měs. | Prošlo |
|---|---|---|---|---|---|---|---|---|---|---|
| long | 2h MACD 19/39/9/signal · d50 · opp | 2019 / +0,31 | 635 / +0,07 | +1,1 | +0,01 | 460 / +0,12 | +0,13 | 64 | 35 | ❌ |
| long | 1h protnutí 2 průměrů sma/30/200/confirm · none · opp | 1178 / +1,67 | 420 / +0,61 | +1,9 | +1,13 | 374 / +0,16 | +0,50 | 245 | 22 | ❌ |
| long | 12h MACD 5/35/5/signal · none · opp | 1591 / +0,32 | 573 / +0,16 | +2,4 | +0,24 | 511 / +0,06 | +0,14 | 73 | 30 | ❌ |
| long | 1h protnutí 2 průměrů sma/40/200/confirm · none · opp | 1071 / +1,82 | 379 / +0,83 | +2,1 | +1,29 | 331 / +0,16 | +0,46 | 246 | 20 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/30/cross · d50 · opp | 2795 / +0,39 | 867 / +0,06 | +0,8 | +0,05 | 617 / +0,10 | +0,34 | 107 | 49 | ❌ |
| long | 6h MACD 12/26/9/signal · none · opp | 1904 / +0,35 | 660 / +0,24 | +2,9 | +0,33 | 636 / +0,04 | +0,13 | 123 | 36 | ❌ |
| long | 6h MACD 19/39/9/signal · none · opp | 1450 / +0,54 | 506 / +0,26 | +2,5 | +0,38 | 480 / +0,11 | +0,18 | 107 | 28 | ❌ |
| long | 4h MACD 5/35/5/signal · d50 · opp | 2312 / +0,18 | 748 / +0,04 | +1,0 | +0,02 | 507 / +0,08 | +0,16 | 43 | 41 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/200/confirm · none · opp | 1773 / +1,05 | 609 / +0,47 | +2,1 | +1,03 | 566 / +0,27 | +0,56 | 253 | 34 | ❌ |
| long | 12h MACD 5/35/5/signal · none · opp_stop | 1591 / +0,41 | 573 / +0,19 | +2,3 | +0,16 | 511 / +0,08 | +0,10 | 93 | 30 | ❌ |
| long | 1h protnutí 2 průměrů sma/30/200/confirm · d50 · opp | 740 / +2,10 | 254 / +0,60 | +1,2 | +0,91 | 178 / +0,87 | +1,51 | 117 | 13 | ❌ |
| long | 1h protnutí 2 průměrů ema/50/60/confirm · none · opp | 1682 / +1,28 | 596 / +0,59 | +2,4 | +0,90 | 574 / +0,14 | +0,23 | 288 | 32 | ❌ |
| long | 1h protnutí 2 průměrů ema/50/200/confirm · none · opp | 1029 / +1,86 | 357 / +0,69 | +2,0 | +1,05 | 332 / +0,05 | +0,40 | 295 | 20 | ❌ |
| long | 2h protnutí 2 průměrů sma/20/200/confirm · none · opp | 633 / +2,38 | 229 / +1,69 | +2,2 | +1,73 | 206 / -0,20 | -0,03 | 192 | 12 | ❌ |
| long | 1h protnutí 2 průměrů sma/20/200/confirm · none · opp | 1381 / +1,36 | 479 / +0,52 | +1,8 | +0,79 | 437 / +0,10 | +0,71 | 289 | 26 | ❌ |
| long | 1h protnutí 2 průměrů ema/40/100/confirm · none · opp | 1515 / +1,24 | 528 / +0,54 | +2,0 | +0,80 | 501 / +0,21 | +0,55 | 291 | 29 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/200/confirm · none · opp | 1075 / +1,58 | 361 / +1,05 | +2,5 | +1,48 | 357 / +0,13 | +0,22 | 180 | 20 | ❌ |
| long | 1h protnutí 2 průměrů ema/40/200/confirm · none · opp | 1125 / +1,64 | 400 / +0,65 | +2,1 | +1,20 | 362 / +0,14 | +0,52 | 283 | 21 | ❌ |
| long | 1h protnutí 2 průměrů sma/40/200/confirm · d50 · opp | 681 / +2,26 | 228 / +0,75 | +1,3 | +1,48 | 156 / +1,44 | +1,38 | 105 | 12 | ❌ |
| long | 4h protnutí 2 průměrů sma/10/100/confirm · none · opp | 558 / +1,95 | 209 / +1,51 | +2,2 | +2,21 | 191 / -0,04 | -0,24 | 123 | 11 | ❌ |
| long | 4h protnutí 2 průměrů sma/10/100/cross · none · opp | 596 / +1,83 | 216 / +1,48 | +2,2 | +2,53 | 199 / -0,03 | +0,13 | 121 | 11 | ❌ |
| long | 1h protnutí 2 průměrů ema/30/100/confirm · none · opp | 1709 / +1,08 | 594 / +0,48 | +2,1 | +0,84 | 573 / +0,21 | +0,32 | 270 | 33 | ❌ |
| long | 2h protnutí 2 průměrů ema/10/30/confirm · none · opp | 2543 / +0,51 | 916 / +0,30 | +2,5 | +0,37 | 866 / +0,10 | +0,11 | 191 | 49 | ❌ |
| long | 4h protnutí 2 průměrů sma/5/30/cross · none · opp | 1771 / +0,57 | 639 / +0,26 | +2,4 | +0,42 | 588 / +0,07 | +0,12 | 137 | 34 | ❌ |
| long | 2h protnutí 2 průměrů ema/40/150/confirm · none · opp | 589 / +2,55 | 225 / +1,68 | +2,0 | +1,97 | 197 / +0,09 | +0,03 | 142 | 11 | ❌ |
| long | 2h protnutí 2 průměrů ema/10/30/cross · none · opp | 2538 / +0,51 | 916 / +0,30 | +2,5 | +0,50 | 866 / +0,10 | +0,18 | 191 | 49 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/60/cross · none · opp | 2311 / +0,65 | 813 / +0,33 | +2,5 | +0,57 | 763 / +0,08 | +0,10 | 210 | 44 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/150/confirm · none · opp | 2011 / +1,01 | 696 / +0,43 | +2,2 | +0,83 | 674 / +0,14 | +0,08 | 302 | 38 | ❌ |
| long | 2h protnutí 2 průměrů sma/10/200/confirm · none · opp | 851 / +1,89 | 292 / +1,27 | +2,4 | +1,69 | 279 / +0,01 | +0,07 | 194 | 16 | ❌ |
| long | 1h protnutí 2 průměrů sma/20/150/confirm · none · opp | 1581 / +1,23 | 530 / +0,61 | +2,2 | +0,79 | 518 / +0,18 | +0,23 | 288 | 30 | ❌ |
| long | 4h MACD 19/39/9/signal · none · opp | 2222 / +0,35 | 767 / +0,24 | +3,1 | +0,30 | 733 / +0,05 | +0,14 | 152 | 42 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/30/confirm · d50 · opp | 2938 / +0,36 | 963 / +0,08 | +1,1 | +0,07 | 681 / +0,18 | +0,31 | 124 | 52 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/200/pullback · none · opp | 832 / +1,73 | 277 / +1,34 | +2,1 | +1,72 | 254 / +0,19 | +0,23 | 139 | 15 | ❌ |
| long | 2h MACD 12/26/9/zero · none · opp | 2512 / +0,50 | 916 / +0,28 | +2,4 | +0,43 | 848 / +0,11 | +0,08 | 187 | 49 | ❌ |
| long | 4h protnutí 2 průměrů sma/10/60/confirm · none · opp | 837 / +1,26 | 298 / +0,77 | +2,0 | +1,22 | 289 / +0,05 | +0,07 | 110 | 16 | ❌ |
| long | 1h protnutí 2 průměrů ema/40/150/confirm · none · opp | 1297 / +1,37 | 464 / +0,55 | +1,8 | +0,91 | 409 / +0,09 | +0,48 | 279 | 25 | ❌ |
| long | 4h protnutí 2 průměrů sma/5/30/confirm · none · opp | 1686 / +0,59 | 600 / +0,28 | +2,5 | +0,39 | 555 / +0,08 | +0,10 | 134 | 32 | ❌ |
| long | 1h protnutí 2 průměrů sma/50/200/confirm · none · opp | 1028 / +1,82 | 346 / +0,71 | +1,8 | +1,27 | 313 / +0,28 | +0,61 | 236 | 19 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/60/confirm · none · opp | 2201 / +0,67 | 775 / +0,33 | +2,4 | +0,69 | 719 / +0,10 | +0,07 | 202 | 42 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/50/cross · none · opp | 2572 / +0,56 | 905 / +0,26 | +2,5 | +0,30 | 838 / +0,08 | +0,15 | 213 | 49 | ❌ |
| long | 2h protnutí 2 průměrů sma/10/60/cross · none · opp | 1777 / +0,82 | 631 / +0,40 | +2,3 | +0,75 | 599 / +0,06 | +0,19 | 210 | 34 | ❌ |
| long | 2h protnutí 2 průměrů sma/10/60/confirm · none · opp | 1699 / +0,85 | 592 / +0,44 | +2,4 | +0,63 | 564 / +0,08 | +0,11 | 201 | 32 | ❌ |
| long | 4h protnutí 2 průměrů ema/20/30/cross · none · opp | 925 / +1,15 | 338 / +0,69 | +2,0 | +1,12 | 312 / +0,01 | +0,07 | 139 | 18 | ❌ |
| long | 12h MACD 19/39/9/signal · none · opp | 698 / +0,78 | 240 / +0,65 | +2,9 | +0,59 | 201 / +0,19 | +0,07 | 49 | 13 | ✅ |
| long | 1h protnutí 2 průměrů ema/50/60/cross · none · opp | 1621 / +1,27 | 582 / +0,56 | +2,2 | +0,89 | 567 / +0,16 | +0,37 | 288 | 31 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/50/confirm · none · opp | 2445 / +0,59 | 859 / +0,27 | +2,5 | +0,36 | 800 / +0,09 | +0,10 | 210 | 47 | ❌ |
| long | 4h momentum ROC 20 · none · opp | 3915 / +0,23 | 1370 / +0,08 | +1,7 | +0,17 | 1167 / +0,03 | +0,09 | 171 | 73 | ❌ |
| long | 4h protnutí 2 průměrů ema/10/60/confirm · none · opp | 846 / +1,33 | 313 / +0,70 | +2,0 | +1,25 | 289 / +0,10 | +0,08 | 126 | 16 | ❌ |
| long | 4h protnutí 2 průměrů ema/20/30/confirm · none · opp | 929 / +1,14 | 338 / +0,69 | +2,0 | +1,17 | 312 / +0,01 | -0,01 | 139 | 18 | ❌ |
| long | 4h protnutí 2 průměrů ema/10/60/cross · none · opp | 844 / +1,34 | 313 / +0,70 | +2,0 | +1,41 | 289 / +0,10 | -0,16 | 126 | 16 | ❌ |
| short | 4h průraz s objemem 20/2.5 · none · target | 549 / +0,24 | 261 / +0,19 | +2,6 | +0,12 | 215 / +0,05 | +0,22 | 45 | 12 | ❌ |
| short | 6h MACD 19/39/9/signal · d50 · opp_stop | 585 / +0,30 | 224 / +0,12 | +1,2 | +0,06 | 278 / +0,10 | +0,13 | 45 | 12 | ❌ |
| short | 4h průraz s objemem 55/2.5 · d50 · target | 270 / +0,28 | 137 / +0,00 | +0,0 | +0,06 | 132 / +0,09 | +0,15 | 18 | 6 | ❌ |
| short | 6h MACD 12/26/9/signal · d50 · opp_stop | 755 / +0,23 | 310 / +0,03 | +0,3 | +0,02 | 366 / -0,02 | +0,14 | 70 | 16 | ❌ |
| short | 4h průraz s objemem 20/1.5 · d200 · target | 526 / +0,19 | 188 / -0,01 | -0,1 | +0,03 | 272 / -0,03 | +0,11 | 44 | 11 | ❌ |
| short | 4h průraz s objemem 55/2.5 · none · target | 363 / +0,23 | 179 / +0,08 | +0,9 | +0,06 | 164 / +0,07 | +0,09 | 30 | 8 | ❌ |
| short | 4h průraz s objemem 20/2.5 · d200 · target | 283 / +0,26 | 115 / +0,07 | +0,6 | -0,04 | 156 / -0,07 | +0,24 | 36 | 6 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/60/pullback · d50 · trail | 1481 / +0,18 | 597 / -0,11 | -1,7 | +0,09 | 569 / +0,02 | +0,03 | 121 | 30 | ❌ |
| short | 4h průraz s objemem 20/2.5 · d50 · target | 324 / +0,23 | 169 / +0,02 | +0,2 | +0,01 | 151 / -0,01 | +0,14 | 29 | 7 | ❌ |
| short | 4h průraz s objemem 55/2.5 · d200 · target | 219 / +0,28 | 91 / +0,02 | +0,1 | +0,10 | 131 / +0,02 | +0,12 | 23 | 5 | ❌ |
| short | 2h Bollinger průraz 50/2.5 · d50 · target | 725 / +0,15 | 291 / +0,11 | +1,5 | +0,03 | 293 / +0,03 | +0,14 | 39 | 15 | ❌ |
| short | 4h MACD 19/39/9/signal · d50 · opp_stop | 916 / +0,20 | 362 / +0,07 | +0,9 | +0,02 | 427 / -0,07 | +0,13 | 82 | 19 | ❌ |
| short | 6h MACD 19/39/9/signal · d50 · opp | 585 / +0,20 | 224 / +0,07 | +0,8 | +0,01 | 278 / +0,01 | +0,08 | 45 | 12 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/100/confirm · d50 · trail | 2117 / +0,13 | 869 / -0,02 | -0,3 | +0,09 | 851 / +0,01 | +0,07 | 97 | 44 | ❌ |
| short | 6h MACD 19/39/9/signal · d200 · opp_stop | 620 / +0,24 | 178 / +0,04 | +0,4 | +0,06 | 339 / +0,07 | +0,12 | 57 | 13 | ❌ |
| short | 1h protnutí 2 průměrů sma/40/50/pullback · d50 · trail | 1678 / +0,15 | 626 / -0,07 | -1,0 | +0,11 | 618 / +0,07 | +0,07 | 112 | 33 | ❌ |
| short | 6h protnutí 2 průměrů ema/50/100/cross · none · target | 178 / +0,27 | 74 / -0,16 | -1,2 | +0,04 | 57 / +0,27 | +0,21 | 26 | 4 | ❌ |
| short | 1h Bollinger průraz 50/2.0 · d50 · trail | 1557 / +0,16 | 656 / +0,07 | +0,9 | +0,09 | 665 / +0,05 | +0,04 | 73 | 33 | ❌ |
| short | 2h protnutí 2 průměrů ema/30/200/cross · none · target | 482 / +0,17 | 202 / +0,21 | +2,5 | +0,09 | 174 / +0,04 | +0,13 | 30 | 10 | ❌ |
| short | 1h protnutí 2 průměrů ema/20/100/cross · d50 · opp_stop | 785 / +0,46 | 327 / +0,15 | +0,9 | -0,06 | 375 / +0,08 | +0,28 | 116 | 17 | ❌ |
| short | 12h protnutí 2 průměrů ema/5/150/cross · none · trail | 162 / +0,37 | 86 / -0,24 | -2,2 | +0,10 | 51 / +0,97 | +0,43 | 33 | 3 | ❌ |
| short | 4h Bollinger průraz 50/2.5 · d200 · target | 302 / +0,21 | 98 / +0,16 | +1,3 | -0,01 | 140 / +0,20 | +0,29 | 23 | 6 | ❌ |
| short | 1h protnutí 2 průměrů sma/30/50/pullback · d50 · trail | 1797 / +0,14 | 706 / +0,04 | +0,6 | +0,08 | 723 / +0,06 | +0,11 | 77 | 37 | ❌ |
| short | 1h Bollinger průraz 50/2.0 · d200 · trail | 1419 / +0,15 | 469 / +0,07 | +0,9 | +0,04 | 729 / +0,02 | +0,06 | 79 | 30 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/60/confirm · d50 · trail | 2279 / +0,12 | 902 / -0,01 | -0,2 | +0,09 | 876 / +0,09 | +0,12 | 76 | 46 | ❌ |
| short | 2h protnutí 2 průměrů sma/20/30/pullback · d50 · trail | 1045 / +0,17 | 373 / -0,02 | -0,2 | +0,11 | 387 / +0,08 | +0,15 | 58 | 21 | ❌ |
| short | 1h protnutí 2 průměrů ema/50/60/confirm · d50 · trail | 2341 / +0,12 | 963 / +0,02 | +0,3 | +0,05 | 1022 / +0,03 | +0,05 | 108 | 49 | ❌ |
| short | 6h MACD 12/26/9/signal · d200 · opp_stop | 790 / +0,17 | 244 / +0,04 | +0,5 | +0,02 | 438 / +0,00 | +0,12 | 69 | 17 | ❌ |
| short | 1h cena × průměr ema/50 · d50 · trail | 2984 / +0,10 | 1190 / +0,04 | +0,7 | +0,07 | 1310 / +0,06 | +0,09 | 114 | 62 | ❌ |
| short | 2h protnutí 2 průměrů ema/40/150/cross · none · target | 496 / +0,15 | 203 / +0,09 | +1,1 | +0,15 | 187 / -0,03 | +0,11 | 38 | 10 | ❌ |
| short | 6h protnutí 2 průměrů ema/20/200/cross · none · target | 178 / +0,25 | 91 / -0,06 | -0,5 | +0,14 | 62 / +0,02 | +0,19 | 25 | 4 | ❌ |
| short | 2h protnutí 2 průměrů sma/5/60/pullback · d50 · trail | 1551 / +0,13 | 637 / -0,01 | -0,1 | +0,12 | 687 / -0,04 | +0,11 | 124 | 33 | ❌ |
| short | 2h protnutí 2 průměrů sma/40/50/cross · d50 · opp_stop | 995 / +0,24 | 407 / -0,01 | -0,1 | +0,06 | 420 / +0,09 | +0,00 | 87 | 21 | ❌ |
| short | 6h MACD 12/26/9/signal · d50 · opp | 755 / +0,14 | 310 / +0,00 | +0,0 | +0,04 | 366 / -0,05 | +0,05 | 67 | 16 | ❌ |
| short | 2h protnutí 2 průměrů sma/10/60/pullback · d50 · opp | 786 / +0,25 | 312 / -0,10 | -1,0 | -0,07 | 327 / +0,05 | +0,33 | 100 | 16 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/100/pullback · d50 · trail | 1638 / +0,14 | 673 / -0,10 | -1,6 | +0,11 | 629 / -0,03 | +0,07 | 138 | 33 | ❌ |
| short | 6h Supertrend 20/3.0 · d200 · opp | 198 / +0,42 | 70 / +0,21 | +1,3 | -0,36 | 115 / +0,15 | +0,56 | 48 | 4 | ❌ |
| short | 1h protnutí 2 průměrů ema/50/60/confirm · d50 · opp | 915 / +0,35 | 385 / -0,13 | -0,9 | +0,04 | 407 / +0,03 | +0,40 | 169 | 19 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/150/cross · d50 · opp_stop | 551 / +0,52 | 233 / +0,14 | +0,7 | +0,05 | 250 / -0,28 | +0,40 | 115 | 12 | ❌ |
| short | 12h MACD 5/35/5/signal · d200 · opp_stop | 652 / +0,13 | 198 / +0,05 | +0,7 | +0,05 | 360 / +0,04 | +0,08 | 39 | 14 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/60/pullback · d50 · trail | 2032 / +0,12 | 849 / -0,02 | -0,3 | +0,09 | 831 / -0,00 | +0,06 | 106 | 42 | ❌ |
| short | 6h protnutí 2 průměrů ema/30/150/cross · none · target | 178 / +0,24 | 84 / +0,03 | +0,2 | +0,22 | 58 / +0,22 | +0,27 | 20 | 4 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/100/pullback · none · trail | 2776 / +0,10 | 1029 / -0,04 | -0,7 | +0,11 | 903 / +0,03 | +0,04 | 152 | 54 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/50/confirm · d50 · opp_stop | 1745 / +0,23 | 722 / -0,02 | -0,2 | -0,04 | 739 / +0,14 | +0,15 | 177 | 36 | ❌ |
| short | 1h protnutí 2 průměrů sma/30/100/pullback · d50 · trail | 2023 / +0,12 | 816 / -0,03 | -0,4 | +0,09 | 849 / -0,07 | +0,04 | 169 | 42 | ❌ |
| short | 6h protnutí 2 průměrů ema/30/100/cross · d50 · target | 155 / +0,26 | 65 / +0,11 | +0,8 | +0,20 | 60 / -0,14 | +0,13 | 21 | 3 | ❌ |
| short | 4h průraz s objemem 20/1.5 · none · target | 1021 / +0,10 | 423 / +0,09 | +1,6 | +0,01 | 366 / -0,00 | +0,08 | 57 | 21 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/200/cross · d50 · opp_stop | 459 / +0,61 | 211 / +0,25 | +1,1 | +0,04 | 239 / -0,47 | +0,48 | 125 | 10 | ❌ |
| short | 2h protnutí 2 průměrů sma/40/50/confirm · d50 · trail | 1240 / +0,14 | 500 / +0,03 | +0,4 | +0,06 | 563 / -0,02 | +0,17 | 90 | 26 | ❌ |
| short | 4h Donchian průraz 20 · d200 · target | 697 / +0,12 | 256 / +0,10 | +1,2 | -0,02 | 334 / +0,04 | +0,13 | 50 | 15 | ❌ |

## 5. Všechny kombinace, které splní kritéria (bez pořadí v IS) – kandidáti, ne důkaz

Splní je **197** z 33868 způsobilých kombinací. Čistou náhodou by to bylo řádově 25 (OOS i HOLDOUT nad p95 ≈ 0,25 %, k tomu t ≥ 2 a kladné IS). Kombinace v rámci rodiny jsou si podobné, takže skutečně nezávislých nálezů je méně.

| Směr | Kombinace | IS Ø R | OOS n / Ø R / t | HOLDOUT n / Ø R | Max. propad R | Obch./měs. | Ø % na obchod (OOS) |
|---|---|---|---|---|---|---|---|
| short | 6h Supertrend 10/3.0 · none · target | +0,03 | 201 / +0,36 / +4,1 | 168 / +0,21 | 50 | 10 | +1,85 |
| short | 6h Supertrend 10/3.0 · d200 · target | +0,14 | 71 / +0,58 / +4,1 | 109 / +0,20 | 19 | 4 | +3,68 |
| short | 6h Supertrend 10/3.0 · d50 · target | +0,09 | 80 / +0,52 / +3,9 | 90 / +0,20 | 24 | 4 | +3,45 |
| long | 1h Bollinger průraz 50/2.5 · none · opp_stop | +0,40 | 733 / +0,57 / +3,2 | 691 / +0,36 | 135 | 43 | +0,78 |
| long | 2h RSI momentum 60 · none · opp | +0,32 | 927 / +0,24 / +3,2 | 871 / +0,09 | 156 | 51 | +0,67 |
| long | 1h Bollinger průraz 50/2.5 · none · opp | +0,43 | 645 / +0,49 / +3,1 | 600 / +0,27 | 141 | 37 | +0,91 |
| long | 1h Bollinger průraz 50/2.0 · none · opp | +0,37 | 906 / +0,37 / +3,0 | 835 / +0,15 | 182 | 50 | +0,67 |
| long | 2h RSI momentum 60 · none · opp_stop | +0,37 | 984 / +0,28 / +3,0 | 917 / +0,16 | 169 | 55 | +0,56 |
| short | 2h protnutí 2 průměrů sma/20/50/cross · none · target | +0,03 | 561 / +0,15 / +2,9 | 526 / +0,10 | 49 | 31 | +0,36 |
| long | 12h MACD 19/39/9/signal · none · opp | +0,78 | 240 / +0,65 / +2,9 | 201 / +0,19 | 49 | 13 | +4,18 |
| long | 2h protnutí 2 průměrů ema/5/50/cross · none · trail | +0,18 | 797 / +0,22 / +2,9 | 773 / +0,10 | 111 | 43 | +0,50 |
| short | 1h protnutí 2 průměrů sma/50/100/cross · none · trail | +0,02 | 575 / +0,23 / +2,9 | 522 / +0,13 | 103 | 31 | +0,37 |
| long | 1h protnutí 2 průměrů sma/5/60/pullback · d50 · opp | +0,49 | 608 / +0,38 / +2,9 | 437 / +0,32 | 117 | 34 | +0,93 |
| long | 1h Bollinger průraz 50/2.0 · none · opp_stop | +0,36 | 1067 / +0,38 / +2,9 | 1004 / +0,18 | 201 | 61 | +0,48 |
| short | 2h Bollinger průraz 50/2.0 · none · target | +0,00 | 690 / +0,13 / +2,8 | 590 / +0,05 | 70 | 36 | +0,26 |
| short | 4h Supertrend 10/3.0 · d50 · trail | +0,06 | 116 / +0,40 / +2,8 | 155 / +0,27 | 36 | 7 | +1,71 |
| long | 1h průraz s objemem 55/1.5 · none · opp | +0,78 | 553 / +0,57 / +2,7 | 469 / +0,50 | 195 | 29 | +0,95 |
| long | 1h průraz s objemem 55/2.5 · none · opp | +1,06 | 434 / +0,65 / +2,7 | 378 / +0,58 | 125 | 22 | +1,18 |
| long | 1h Supertrend 20/3.0 · none · opp | +0,27 | 1223 / +0,23 / +2,7 | 1153 / +0,09 | 209 | 67 | +0,47 |
| long | 1h protnutí 2 průměrů ema/10/100/cross · none · opp_stop | +0,57 | 957 / +0,37 / +2,6 | 936 / +0,22 | 249 | 52 | +0,48 |
| long | 2h Bollinger průraz 50/2.0 · none · opp | +0,77 | 448 / +0,46 / +2,6 | 393 / +0,35 | 120 | 24 | +1,21 |
| short | 6h protnutí 2 průměrů ema/10/50/cross · none · target | +0,06 | 207 / +0,22 / +2,6 | 188 / +0,14 | 37 | 10 | +1,58 |
| long | 2h protnutí 2 průměrů sma/5/150/cross · none · trail | +0,20 | 434 / +0,28 / +2,6 | 403 / +0,28 | 60 | 23 | +0,69 |
| long | 12h MACD 19/39/9/signal · none · opp_stop | +0,89 | 240 / +0,76 / +2,6 | 201 / +0,25 | 44 | 13 | +3,72 |
| long | 2h protnutí 2 průměrů ema/10/50/cross · none · trail | +0,13 | 634 / +0,23 / +2,6 | 626 / +0,08 | 121 | 35 | +0,52 |
| long | 1h protnutí 2 průměrů sma/5/50/pullback · d50 · opp | +0,41 | 678 / +0,29 / +2,6 | 484 / +0,29 | 112 | 37 | +0,79 |
| long | 6h protnutí 2 průměrů ema/50/60/cross · none · target | +0,06 | 88 / +0,34 / +2,6 | 84 / +0,40 | 29 | 5 | +1,80 |
| long | 2h protnutí 2 průměrů sma/5/60/cross · none · trail | +0,18 | 715 / +0,20 / +2,6 | 685 / +0,09 | 142 | 39 | +0,56 |
| long | 6h Bollinger průraz 50/2.5 · none · target | +0,20 | 170 / +0,25 / +2,6 | 135 / +0,07 | 35 | 10 | +1,41 |
| long | 1h Bollinger průraz 50/2.5 · none · trail | +0,20 | 738 / +0,22 / +2,5 | 685 / +0,15 | 94 | 43 | +0,44 |
| long | 1h Bollinger průraz 50/2.0 · none · trail | +0,16 | 1057 / +0,17 / +2,5 | 974 / +0,08 | 133 | 60 | +0,35 |
| long | 6h RSI momentum 60 · none · opp | +0,77 | 310 / +0,52 / +2,5 | 283 / +0,19 | 77 | 17 | +2,28 |
| long | 6h Bollinger průraz 20/2.0 · none · opp | +0,61 | 322 / +0,42 / +2,5 | 262 / +0,32 | 60 | 17 | +1,69 |
| short | 1h protnutí 2 průměrů sma/40/50/cross · none · trail | +0,02 | 1251 / +0,13 / +2,5 | 1151 / +0,07 | 119 | 70 | +0,09 |
| long | 6h RSI momentum 60 · none · opp_stop | +0,87 | 325 / +0,64 / +2,5 | 302 / +0,27 | 93 | 18 | +2,13 |
| long | 4h Bollinger průraz 20/2.0 · none · opp | +0,45 | 487 / +0,25 / +2,5 | 412 / +0,18 | 84 | 26 | +0,90 |
| short | 2h protnutí 2 průměrů sma/30/50/cross · none · target | +0,04 | 553 / +0,13 / +2,5 | 529 / +0,07 | 62 | 31 | +0,44 |
| long | 1h průraz s objemem 55/2.5 · none · opp_stop | +0,69 | 546 / +0,57 / +2,5 | 489 / +0,48 | 106 | 28 | +0,78 |
| long | 1h Donchian průraz 100 · none · opp_stop | +0,91 | 547 / +0,63 / +2,4 | 472 / +0,60 | 187 | 30 | +1,01 |
| long | 2h Bollinger průraz 50/2.0 · none · opp_stop | +0,70 | 535 / +0,46 / +2,4 | 482 / +0,37 | 161 | 30 | +0,92 |

Podle rodiny a timeframu: protnutí 2 průměrů 2h long: 21; protnutí 2 průměrů 1h long: 14; Bollinger průraz 2h long: 12; protnutí 2 průměrů 6h long: 12; protnutí 2 průměrů 12h long: 10; Bollinger průraz 1h long: 10; protnutí 2 průměrů 4h long: 10; Bollinger průraz 6h long: 9; Bollinger průraz 4h long: 8; protnutí 2 průměrů 1h short: 7; Keltner průraz 6h long: 7; Bollinger průraz 12h long: 6; průraz s objemem 1h long: 6; Donchian průraz 6h long: 5; Donchian průraz 1h long: 4.

## Závěr

✅ **Předem stanovené pravidlo splnilo 1 kombinací:** long 12h MACD 19/39/9/signal · none · opp. Další krok je papírové ověření vedle skeneru, ne ostré zapnutí.

## Ověření a interpretace (doplněno 27. 10. 2026, výběr se tím nemění)

**Nezávislý přepočet** kandidáta long 12H MACD 19/39/9 (samostatný kód `research/experiments/atlas_verify.py`,
výstup `reports/atlas_verify.txt`) dal stejná čísla: IS +0,78 R (n 698), OOS +0,65 R (n 240), HOLDOUT +0,19 R (n 201).
Vstup o svíčku později: +0,78 / +0,59 / +0,19 R → žádný pohled do budoucnosti. Kladný na všech 8 mincích
(Ø +0,45 až +0,82 R). Po letech: 2022 −14 R, 2025 +5 R, ostatní roky výrazně v plusu – vydělává v trendu, v medvědím
a bočním trhu stojí. Úspěšnost 35–40 %, zisk dělají velké obchody (medián držení 8 dní).
Účet při riziku 0,5 % na obchod, 8 mincí souběžně: celé období ~+58 % ročně, max. propad 22 %; HOLDOUT ~+16 % ročně,
propad 15 %. Při riziku 0,25 %: ~+26 % ročně, propad 12 %. Jen historie, poplatky 0,05 %/stranu, funding nezapočten.

**Rodiny:** průrazové longy (Bollinger, Keltner, Donchian, průraz s objemem) porážejí vlastní náhodu v OOS i HOLDOUT
u 32–51 % kombinací (náhodou ~0,25 %) – to je nejsilnější a nejširší zjištění atlasu: **kupovat sílu funguje na 1H–12H
i po poplatcích MEXC.** Návratové strategie (Bollinger návrat, RSI návrat, Stochastic, sweep & reclaim) jsou u longu
pod náhodou. Shorty: slabé, výjimkou jsou rychlé cíle u Supertrendu a Keltneru na 2H–6H (kandidáti, ne důkaz).
15M: po poplatcích převážně ztrátové (OOS > 0 jen 22 % longů). Nižší poplatky MEXC proti dřívějším 0,15 % zvyšují
počet kandidátů z 65 na 215.

Celá tabulka: `reports/atlas/<timeframe>.csv.gz` (všechny scénáře poplatků i náhodná srovnání).

Nejde o finanční poradenství.