# Atlas strategií – 15 rodin, 7 timeframů, poplatky MEXC (27. 10. 2026)

Otázka: je mezi běžnými pravidlovými strategiemi na kterémkoli timeframu něco, co po poplatcích MEXC vydělává spolehlivěji než náhoda? Metoda stanovená předem je v hlavičce `research/experiments/strategy_atlas.py`.

- **42 048 kombinací** (15 rodin, 248 variant × 7 timeframů × 3 filtry × 4 výstupy × long/short), 8 mincí.
- 12h: 5952 kombinací, 833 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 15m: 5952 kombinací, 2824 s, data od BTC 01/2022, ETH 01/2022, SOL 01/2022, XRP 01/2022, ADA 01/2022, LINK 01/2022, AVAX 01/2022, DOGE 01/2022
- 1d: 5952 kombinací, 820 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 1h: 5952 kombinací, 1085 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 2h: 5952 kombinací, 1187 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 4h: 5952 kombinací, 1146 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 6h: 5952 kombinací, 1047 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- sent_1d: 192 kombinací, 1006 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- sent_4h: 192 kombinací, 1 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- Poplatky na stranu: **MEXC futures taker 0,02 % + skluz 0,03 % = 0,05 % (rozhoduje)**; MEXC spot taker 0,08 %; maker 0 % (optimistická mez); 0,15 % (dřívější testy). Funding nezapočten. Poplatky MEXC podle [MEXC, 11/2025](https://www.mexc.com/ru-RU/crypto-pulse/article/mexc-trading-fees-complete-guide-39643).
- IS do 12/2023 (15M od 1/2022), OOS 1/2024–6/2025, HOLDOUT 7/2025–dnes. R = výsledek po poplatcích / riziko (vzdálenost stopu; bez stopu 2 ATR).

## 1. Mají rodiny strategií výhodu? (hlavní scénář poplatků)

„Nad náhodou“ = podíl kombinací, jejichž Ø R v daném období je nad mediánem jejich vlastních náhodných vstupů (bez výhody by to bylo ~50 %). „Obě nad p95“ = OOS i HOLDOUT nad 95. percentilem náhody (čistou náhodou ~0,25 %).

| Rodina | Směr | Kombinací | OOS > 0 | HOLDOUT > 0 | OOS nad náhodou | HOLDOUT nad náhodou | Obě nad p95 | Medián OOS R | Medián HOLDOUT R |
|---|---|---|---|---|---|---|---|---|---|
| Bollinger průraz | long | 336 | 81% | 74% | 93% | 91% | 52,7% | +0,25 | +0,16 |
| Bollinger průraz | short | 336 | 32% | 75% | 53% | 73% | 12,2% | -0,06 | +0,10 |
| Bollinger návrat | long | 336 | 21% | 26% | 17% | 33% | 0,3% | -0,11 | -0,09 |
| Bollinger návrat | short | 336 | 33% | 54% | 46% | 35% | 2,1% | -0,05 | +0,02 |
| svíčkové vzory | long | 168 | 50% | 38% | 58% | 55% | 1,2% | -0,00 | -0,02 |
| svíčkové vzory | short | 168 | 23% | 68% | 61% | 54% | 2,4% | -0,06 | +0,06 |
| Donchian průraz | long | 420 | 80% | 61% | 94% | 82% | 35,2% | +0,25 | +0,06 |
| Donchian průraz | short | 420 | 30% | 69% | 48% | 51% | 1,7% | -0,08 | +0,10 |
| strach a chamtivost | long | 192 | 35% | 21% | 29% | 20% | 0,5% | -0,16 | -0,34 |
| strach a chamtivost | short | 192 | 41% | 18% | 46% | 17% | 1,0% | +0,04 | -0,18 |
| Keltner průraz | long | 252 | 80% | 69% | 94% | 89% | 48,0% | +0,19 | +0,12 |
| Keltner průraz | short | 252 | 40% | 65% | 54% | 75% | 10,3% | -0,05 | +0,10 |
| protnutí 2 průměrů | long | 16128 | 66% | 52% | 70% | 68% | 9,2% | +0,16 | +0,01 |
| protnutí 2 průměrů | short | 16128 | 31% | 73% | 69% | 51% | 5,2% | -0,07 | +0,13 |
| MACD | long | 504 | 63% | 50% | 76% | 58% | 8,7% | +0,10 | -0,00 |
| MACD | short | 504 | 45% | 64% | 79% | 41% | 6,2% | -0,01 | +0,04 |
| cena × průměr | long | 840 | 54% | 50% | 55% | 50% | 4,6% | +0,02 | +0,00 |
| cena × průměr | short | 840 | 37% | 69% | 88% | 45% | 9,3% | -0,02 | +0,05 |
| momentum ROC | long | 336 | 56% | 48% | 55% | 54% | 4,2% | +0,02 | -0,00 |
| momentum ROC | short | 336 | 32% | 65% | 80% | 38% | 8,3% | -0,04 | +0,04 |
| RSI momentum | long | 252 | 62% | 60% | 78% | 69% | 13,9% | +0,06 | +0,02 |
| RSI momentum | short | 252 | 37% | 76% | 88% | 57% | 7,5% | -0,02 | +0,06 |
| RSI návrat | long | 336 | 23% | 18% | 23% | 26% | 0,0% | -0,09 | -0,11 |
| RSI návrat | short | 336 | 24% | 53% | 38% | 44% | 6,8% | -0,07 | +0,02 |
| Stochastic | long | 168 | 22% | 14% | 19% | 15% | 0,0% | -0,11 | -0,10 |
| Stochastic | short | 168 | 11% | 61% | 27% | 60% | 1,8% | -0,07 | +0,03 |
| Supertrend | long | 252 | 67% | 50% | 79% | 59% | 4,4% | +0,14 | -0,00 |
| Supertrend | short | 252 | 55% | 75% | 80% | 52% | 4,8% | +0,02 | +0,08 |
| sweep & reclaim | long | 168 | 34% | 10% | 22% | 11% | 0,0% | -0,10 | -0,14 |
| sweep & reclaim | short | 168 | 12% | 62% | 26% | 39% | 1,2% | -0,11 | +0,03 |
| průraz s objemem | long | 336 | 80% | 67% | 96% | 83% | 37,8% | +0,36 | +0,16 |
| průraz s objemem | short | 336 | 27% | 69% | 42% | 58% | 5,7% | -0,14 | +0,10 |

## 2. Podle timeframu (všechny rodiny dohromady)

| TF | Směr | OOS > 0 | HOLDOUT > 0 | OOS nad náhodou | HOLDOUT nad náhodou | Medián OOS R | Medián obchodů/měs. |
|---|---|---|---|---|---|---|---|
| 15m | long | 22% | 24% | 80% | 62% | -0,08 | 146 |
| 15m | short | 32% | 2% | 89% | 50% | -0,03 | 203 |
| 1h | long | 61% | 60% | 77% | 56% | +0,05 | 40 |
| 1h | short | 54% | 61% | 72% | 43% | +0,01 | 44 |
| 2h | long | 69% | 61% | 71% | 62% | +0,10 | 20 |
| 2h | short | 41% | 79% | 61% | 34% | -0,02 | 22 |
| 4h | long | 75% | 63% | 70% | 65% | +0,17 | 10 |
| 4h | short | 32% | 82% | 67% | 37% | -0,07 | 11 |
| 6h | long | 77% | 59% | 60% | 69% | +0,44 | 7 |
| 6h | short | 28% | 89% | 70% | 58% | -0,10 | 8 |
| 12h | long | 76% | 56% | 63% | 78% | +0,48 | 3 |
| 12h | short | 22% | 92% | 64% | 63% | -0,18 | 4 |
| 1d | long | 65% | 35% | 58% | 65% | +0,30 | 2 |
| 1d | short | 12% | 90% | 51% | 67% | -0,28 | 2 |

## 3. Kolik dělají poplatky

Podíl všech kombinací s kladným Ø R v OOS a v HOLDOUT podle výše poplatků:

| Poplatky na stranu | OOS > 0 long | OOS > 0 short | HOLDOUT > 0 long | HOLDOUT > 0 short | Projde pravidlem (ze všech) |
|---|---|---|---|---|---|
| 0 % (maker, optimisticky) | 76% | 47% | 64% | 90% | 1033 z 33868 |
| 0,05 % (MEXC futures taker) | 64% | 31% | 51% | 71% | 239 z 33868 |
| 0,08 % (MEXC spot taker) | 60% | 23% | 46% | 64% | 162 z 33868 |
| 0,15 % (dřívější testy) | 54% | 14% | 37% | 55% | 69 z 33868 |

## 4. Výběr podle předem stanoveného pravidla (50 nejlepších podle IS t-statistiky na směr)

| Směr | Kombinace | IS n / Ø R | OOS n / Ø R | OOS t | Náhoda OOS p95 | HOLDOUT n / Ø R | Náhoda HOLD p95 | Max. propad R | Obch./měs. | Prošlo |
|---|---|---|---|---|---|---|---|---|---|---|
| long | 2h MACD 19/39/9/signal · d50 · opp | 2019 / +0,31 | 635 / +0,07 | +1,1 | -0,02 | 460 / +0,12 | +0,09 | 64 | 35 | ❌ |
| long | 1h protnutí 2 průměrů sma/30/200/confirm · none · opp | 1178 / +1,67 | 420 / +0,61 | +1,9 | +0,93 | 385 / +0,07 | +0,54 | 245 | 22 | ❌ |
| long | 12h MACD 5/35/5/signal · none · opp | 1591 / +0,32 | 573 / +0,16 | +2,4 | +0,23 | 537 / +0,02 | +0,08 | 73 | 30 | ❌ |
| long | 1h protnutí 2 průměrů sma/40/200/confirm · none · opp | 1071 / +1,82 | 379 / +0,83 | +2,1 | +1,02 | 337 / +0,09 | +0,23 | 246 | 20 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/30/cross · d50 · opp | 2795 / +0,39 | 867 / +0,06 | +0,8 | +0,06 | 618 / +0,10 | +0,35 | 107 | 48 | ❌ |
| long | 6h MACD 12/26/9/signal · none · opp | 1904 / +0,35 | 660 / +0,24 | +2,9 | +0,30 | 668 / -0,00 | +0,13 | 123 | 36 | ❌ |
| long | 6h MACD 19/39/9/signal · none · opp | 1450 / +0,54 | 506 / +0,26 | +2,5 | +0,42 | 500 / +0,06 | +0,11 | 107 | 28 | ❌ |
| long | 4h MACD 5/35/5/signal · d50 · opp | 2312 / +0,18 | 748 / +0,04 | +1,0 | +0,03 | 508 / +0,08 | +0,10 | 43 | 40 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/200/confirm · none · opp | 1773 / +1,05 | 609 / +0,47 | +2,1 | +0,79 | 581 / +0,20 | +0,47 | 253 | 33 | ❌ |
| long | 12h MACD 5/35/5/signal · none · opp_stop | 1591 / +0,41 | 573 / +0,19 | +2,3 | +0,17 | 537 / +0,04 | +0,12 | 93 | 30 | ❌ |
| long | 1h protnutí 2 průměrů sma/30/200/confirm · d50 · opp | 740 / +2,10 | 254 / +0,60 | +1,2 | +1,39 | 178 / +0,87 | +1,96 | 117 | 13 | ❌ |
| long | 1h protnutí 2 průměrů ema/50/60/confirm · none · opp | 1682 / +1,28 | 596 / +0,59 | +2,4 | +1,12 | 587 / +0,07 | +0,34 | 288 | 32 | ❌ |
| long | 1h protnutí 2 průměrů ema/50/200/confirm · none · opp | 1029 / +1,86 | 357 / +0,69 | +2,0 | +0,89 | 337 / +0,00 | +0,19 | 295 | 19 | ❌ |
| long | 2h protnutí 2 průměrů sma/20/200/confirm · none · opp | 633 / +2,38 | 229 / +1,69 | +2,2 | +2,04 | 208 / -0,23 | -0,20 | 192 | 12 | ❌ |
| long | 1h protnutí 2 průměrů sma/20/200/confirm · none · opp | 1381 / +1,36 | 479 / +0,52 | +1,8 | +1,03 | 447 / +0,03 | +0,50 | 289 | 26 | ❌ |
| long | 1h protnutí 2 průměrů ema/40/100/confirm · none · opp | 1515 / +1,24 | 528 / +0,54 | +2,0 | +0,94 | 513 / +0,13 | +0,32 | 291 | 29 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/200/confirm · none · opp | 1075 / +1,58 | 361 / +1,05 | +2,5 | +1,42 | 362 / +0,10 | -0,08 | 180 | 20 | ❌ |
| long | 1h protnutí 2 průměrů ema/40/200/confirm · none · opp | 1125 / +1,64 | 400 / +0,65 | +2,1 | +0,83 | 369 / +0,07 | +0,36 | 283 | 21 | ❌ |
| long | 1h protnutí 2 průměrů sma/40/200/confirm · d50 · opp | 681 / +2,26 | 228 / +0,75 | +1,3 | +1,46 | 157 / +1,40 | +1,56 | 105 | 12 | ❌ |
| long | 4h protnutí 2 průměrů sma/10/100/confirm · none · opp | 558 / +1,95 | 209 / +1,51 | +2,2 | +2,36 | 194 / -0,07 | -0,04 | 123 | 11 | ❌ |
| long | 4h protnutí 2 průměrů sma/10/100/cross · none · opp | 596 / +1,83 | 216 / +1,48 | +2,2 | +1,99 | 203 / -0,06 | -0,33 | 121 | 11 | ❌ |
| long | 1h protnutí 2 průměrů ema/30/100/confirm · none · opp | 1709 / +1,08 | 594 / +0,48 | +2,1 | +0,73 | 587 / +0,14 | +0,08 | 270 | 33 | ❌ |
| long | 2h protnutí 2 průměrů ema/10/30/confirm · none · opp | 2543 / +0,51 | 916 / +0,30 | +2,5 | +0,34 | 881 / +0,08 | +0,09 | 191 | 49 | ❌ |
| long | 4h protnutí 2 průměrů sma/5/30/cross · none · opp | 1771 / +0,57 | 639 / +0,26 | +2,4 | +0,38 | 606 / +0,03 | +0,04 | 137 | 34 | ❌ |
| long | 2h protnutí 2 průměrů ema/40/150/confirm · none · opp | 589 / +2,55 | 225 / +1,68 | +2,0 | +1,97 | 198 / +0,08 | -0,35 | 142 | 11 | ❌ |
| long | 2h protnutí 2 průměrů ema/10/30/cross · none · opp | 2538 / +0,51 | 916 / +0,30 | +2,5 | +0,39 | 881 / +0,08 | +0,09 | 191 | 49 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/60/cross · none · opp | 2311 / +0,65 | 813 / +0,33 | +2,5 | +0,55 | 780 / +0,05 | -0,03 | 210 | 44 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/150/confirm · none · opp | 2011 / +1,01 | 696 / +0,43 | +2,2 | +0,80 | 690 / +0,08 | +0,08 | 302 | 38 | ❌ |
| long | 2h protnutí 2 průměrů sma/10/200/confirm · none · opp | 851 / +1,89 | 292 / +1,27 | +2,4 | +1,77 | 283 / -0,02 | -0,06 | 194 | 16 | ❌ |
| long | 1h protnutí 2 průměrů sma/20/150/confirm · none · opp | 1581 / +1,23 | 530 / +0,61 | +2,2 | +0,71 | 531 / +0,11 | +0,17 | 288 | 30 | ❌ |
| long | 4h MACD 19/39/9/signal · none · opp | 2222 / +0,35 | 767 / +0,24 | +3,1 | +0,24 | 760 / -0,00 | +0,08 | 152 | 42 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/30/confirm · d50 · opp | 2938 / +0,36 | 963 / +0,08 | +1,1 | +0,05 | 684 / +0,16 | +0,28 | 124 | 52 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/200/pullback · none · opp | 832 / +1,73 | 277 / +1,34 | +2,1 | +1,28 | 258 / +0,16 | +0,04 | 139 | 15 | ✅ |
| long | 2h MACD 12/26/9/zero · none · opp | 2512 / +0,50 | 916 / +0,28 | +2,4 | +0,34 | 861 / +0,08 | -0,02 | 187 | 48 | ❌ |
| long | 4h protnutí 2 průměrů sma/10/60/confirm · none · opp | 837 / +1,26 | 298 / +0,77 | +2,0 | +1,27 | 297 / -0,00 | +0,04 | 110 | 16 | ❌ |
| long | 1h protnutí 2 průměrů ema/40/150/confirm · none · opp | 1297 / +1,37 | 464 / +0,55 | +1,8 | +1,08 | 419 / +0,01 | +0,53 | 279 | 25 | ❌ |
| long | 4h protnutí 2 průměrů sma/5/30/confirm · none · opp | 1686 / +0,59 | 600 / +0,28 | +2,5 | +0,48 | 573 / +0,03 | +0,03 | 134 | 32 | ❌ |
| long | 1h protnutí 2 průměrů sma/50/200/confirm · none · opp | 1028 / +1,82 | 346 / +0,71 | +1,8 | +1,42 | 320 / +0,20 | +0,64 | 236 | 19 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/60/confirm · none · opp | 2201 / +0,67 | 775 / +0,33 | +2,4 | +0,56 | 736 / +0,06 | +0,10 | 202 | 42 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/50/cross · none · opp | 2572 / +0,56 | 905 / +0,26 | +2,5 | +0,31 | 857 / +0,06 | -0,03 | 213 | 49 | ❌ |
| long | 2h protnutí 2 průměrů sma/10/60/cross · none · opp | 1777 / +0,82 | 631 / +0,40 | +2,3 | +0,66 | 611 / +0,02 | +0,08 | 210 | 34 | ❌ |
| long | 2h protnutí 2 průměrů sma/10/60/confirm · none · opp | 1699 / +0,85 | 592 / +0,44 | +2,4 | +0,54 | 576 / +0,04 | +0,04 | 201 | 32 | ❌ |
| long | 4h protnutí 2 průměrů ema/20/30/cross · none · opp | 925 / +1,15 | 338 / +0,69 | +2,0 | +1,21 | 320 / -0,03 | -0,08 | 139 | 18 | ❌ |
| long | 12h MACD 19/39/9/signal · none · opp | 698 / +0,78 | 240 / +0,65 | +2,9 | +0,82 | 214 / +0,10 | -0,03 | 49 | 13 | ❌ |
| long | 1h protnutí 2 průměrů ema/50/60/cross · none · opp | 1621 / +1,27 | 582 / +0,56 | +2,2 | +0,88 | 580 / +0,09 | +0,25 | 288 | 31 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/50/confirm · none · opp | 2445 / +0,59 | 859 / +0,27 | +2,5 | +0,40 | 818 / +0,06 | +0,08 | 210 | 47 | ❌ |
| long | 4h momentum ROC 20 · none · opp | 3915 / +0,23 | 1370 / +0,08 | +1,7 | +0,15 | 1211 / +0,00 | +0,06 | 171 | 73 | ❌ |
| long | 4h protnutí 2 průměrů ema/10/60/confirm · none · opp | 846 / +1,33 | 313 / +0,70 | +2,0 | +1,46 | 294 / +0,07 | -0,03 | 126 | 16 | ❌ |
| long | 4h protnutí 2 průměrů ema/20/30/confirm · none · opp | 929 / +1,14 | 338 / +0,69 | +2,0 | +1,29 | 320 / -0,03 | +0,03 | 139 | 18 | ❌ |
| long | 4h protnutí 2 průměrů ema/10/60/cross · none · opp | 844 / +1,34 | 313 / +0,70 | +2,0 | +1,24 | 294 / +0,07 | -0,23 | 126 | 16 | ❌ |
| short | 4h průraz s objemem 20/2.5 · none · target | 549 / +0,24 | 261 / +0,19 | +2,6 | +0,04 | 238 / +0,09 | +0,19 | 49 | 12 | ❌ |
| short | 6h MACD 19/39/9/signal · d50 · opp_stop | 585 / +0,30 | 224 / +0,12 | +1,2 | +0,02 | 300 / +0,18 | +0,22 | 45 | 13 | ❌ |
| short | 4h průraz s objemem 55/2.5 · d50 · target | 270 / +0,28 | 137 / +0,00 | +0,0 | -0,01 | 152 / +0,11 | +0,13 | 23 | 6 | ❌ |
| short | 6h MACD 12/26/9/signal · d50 · opp_stop | 755 / +0,23 | 310 / +0,03 | +0,3 | +0,03 | 393 / +0,01 | +0,18 | 70 | 16 | ❌ |
| short | 4h průraz s objemem 20/1.5 · d200 · target | 526 / +0,19 | 188 / -0,01 | -0,1 | +0,02 | 294 / +0,01 | +0,21 | 44 | 11 | ❌ |
| short | 4h průraz s objemem 55/2.5 · none · target | 363 / +0,23 | 179 / +0,08 | +0,9 | +0,14 | 185 / +0,09 | +0,22 | 36 | 8 | ❌ |
| short | 4h průraz s objemem 20/2.5 · d200 · target | 283 / +0,26 | 115 / +0,07 | +0,6 | +0,05 | 175 / +0,01 | +0,18 | 38 | 6 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/60/pullback · d50 · trail | 1481 / +0,18 | 597 / -0,11 | -1,7 | +0,09 | 605 / +0,05 | +0,10 | 121 | 30 | ❌ |
| short | 4h průraz s objemem 20/2.5 · d50 · target | 324 / +0,23 | 169 / +0,02 | +0,2 | +0,07 | 173 / +0,06 | +0,18 | 32 | 8 | ❌ |
| short | 4h průraz s objemem 55/2.5 · d200 · target | 219 / +0,28 | 91 / +0,02 | +0,1 | +0,14 | 148 / +0,07 | +0,25 | 26 | 5 | ❌ |
| short | 2h Bollinger průraz 50/2.5 · d50 · target | 725 / +0,15 | 291 / +0,11 | +1,5 | +0,03 | 318 / +0,03 | +0,16 | 44 | 15 | ❌ |
| short | 4h MACD 19/39/9/signal · d50 · opp_stop | 916 / +0,20 | 362 / +0,07 | +0,9 | -0,01 | 458 / -0,07 | +0,15 | 82 | 20 | ❌ |
| short | 6h MACD 19/39/9/signal · d50 · opp | 585 / +0,20 | 224 / +0,07 | +0,8 | +0,11 | 300 / +0,07 | +0,16 | 45 | 13 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/100/confirm · d50 · trail | 2117 / +0,13 | 869 / -0,02 | -0,3 | +0,08 | 904 / +0,03 | +0,12 | 110 | 44 | ❌ |
| short | 6h MACD 19/39/9/signal · d200 · opp_stop | 620 / +0,24 | 178 / +0,04 | +0,4 | +0,08 | 355 / +0,14 | +0,13 | 57 | 13 | ❌ |
| short | 1h protnutí 2 průměrů sma/40/50/pullback · d50 · trail | 1678 / +0,15 | 626 / -0,07 | -1,0 | +0,09 | 664 / +0,13 | +0,16 | 112 | 34 | ❌ |
| short | 6h protnutí 2 průměrů ema/50/100/cross · none · target | 178 / +0,27 | 74 / -0,16 | -1,2 | +0,22 | 57 / +0,28 | +0,23 | 26 | 3 | ❌ |
| short | 1h Bollinger průraz 50/2.0 · d50 · trail | 1557 / +0,16 | 656 / +0,07 | +0,9 | +0,08 | 726 / +0,03 | +0,12 | 102 | 33 | ❌ |
| short | 2h protnutí 2 průměrů ema/30/200/cross · none · target | 482 / +0,17 | 202 / +0,21 | +2,5 | +0,11 | 175 / +0,04 | +0,11 | 30 | 10 | ❌ |
| short | 1h protnutí 2 průměrů ema/20/100/cross · d50 · opp_stop | 785 / +0,46 | 327 / +0,15 | +0,9 | -0,14 | 391 / +0,10 | +0,42 | 116 | 17 | ❌ |
| short | 12h protnutí 2 průměrů ema/5/150/cross · none · trail | 162 / +0,37 | 86 / -0,24 | -2,2 | +0,04 | 53 / +1,16 | +0,56 | 33 | 3 | ❌ |
| short | 4h Bollinger průraz 50/2.5 · d200 · target | 302 / +0,21 | 98 / +0,16 | +1,3 | +0,02 | 150 / +0,20 | +0,14 | 23 | 6 | ❌ |
| short | 1h protnutí 2 průměrů sma/30/50/pullback · d50 · trail | 1797 / +0,14 | 706 / +0,04 | +0,6 | +0,06 | 774 / +0,11 | +0,11 | 77 | 37 | ❌ |
| short | 1h Bollinger průraz 50/2.0 · d200 · trail | 1419 / +0,15 | 469 / +0,07 | +0,9 | +0,02 | 782 / +0,01 | +0,11 | 101 | 30 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/60/confirm · d50 · trail | 2279 / +0,12 | 902 / -0,01 | -0,2 | +0,08 | 930 / +0,10 | +0,08 | 85 | 46 | ❌ |
| short | 2h protnutí 2 průměrů sma/20/30/pullback · d50 · trail | 1045 / +0,17 | 373 / -0,02 | -0,2 | +0,09 | 418 / +0,14 | +0,21 | 58 | 21 | ❌ |
| short | 1h protnutí 2 průměrů ema/50/60/confirm · d50 · trail | 2341 / +0,12 | 963 / +0,02 | +0,3 | +0,10 | 1077 / +0,04 | +0,09 | 108 | 50 | ❌ |
| short | 6h MACD 12/26/9/signal · d200 · opp_stop | 790 / +0,17 | 244 / +0,04 | +0,5 | +0,00 | 459 / +0,04 | +0,13 | 69 | 17 | ❌ |
| short | 1h cena × průměr ema/50 · d50 · trail | 2984 / +0,10 | 1190 / +0,04 | +0,7 | +0,09 | 1366 / +0,08 | +0,10 | 114 | 63 | ❌ |
| short | 2h protnutí 2 průměrů ema/40/150/cross · none · target | 496 / +0,15 | 203 / +0,09 | +1,1 | +0,09 | 188 / -0,02 | +0,07 | 38 | 10 | ❌ |
| short | 6h protnutí 2 průměrů ema/20/200/cross · none · target | 178 / +0,25 | 91 / -0,06 | -0,5 | +0,26 | 64 / +0,04 | +0,25 | 25 | 4 | ❌ |
| short | 2h protnutí 2 průměrů sma/5/60/pullback · d50 · trail | 1551 / +0,13 | 637 / -0,01 | -0,1 | +0,09 | 720 / +0,00 | +0,23 | 124 | 33 | ❌ |
| short | 2h protnutí 2 průměrů sma/40/50/cross · d50 · opp_stop | 995 / +0,24 | 407 / -0,01 | -0,1 | -0,01 | 436 / +0,25 | +0,20 | 87 | 21 | ❌ |
| short | 6h MACD 12/26/9/signal · d50 · opp | 755 / +0,14 | 310 / +0,00 | +0,0 | +0,01 | 393 / -0,01 | +0,13 | 67 | 16 | ❌ |
| short | 2h protnutí 2 průměrů sma/10/60/pullback · d50 · opp | 786 / +0,25 | 312 / -0,10 | -1,0 | +0,07 | 338 / +0,17 | +0,48 | 100 | 16 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/100/pullback · d50 · trail | 1638 / +0,14 | 673 / -0,10 | -1,6 | +0,08 | 666 / +0,00 | +0,12 | 148 | 34 | ❌ |
| short | 6h Supertrend 20/3.0 · d200 · opp | 198 / +0,42 | 70 / +0,21 | +1,3 | -0,46 | 117 / +0,19 | +0,64 | 48 | 4 | ❌ |
| short | 1h protnutí 2 průměrů ema/50/60/confirm · d50 · opp | 915 / +0,35 | 385 / -0,13 | -0,9 | -0,09 | 424 / +0,10 | +0,58 | 169 | 19 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/150/cross · d50 · opp_stop | 551 / +0,52 | 233 / +0,14 | +0,7 | -0,02 | 263 / -0,12 | +0,35 | 116 | 12 | ❌ |
| short | 12h MACD 5/35/5/signal · d200 · opp_stop | 652 / +0,13 | 198 / +0,05 | +0,7 | +0,02 | 377 / +0,09 | +0,12 | 39 | 14 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/60/pullback · d50 · trail | 2032 / +0,12 | 849 / -0,02 | -0,3 | +0,10 | 888 / +0,04 | +0,07 | 106 | 43 | ❌ |
| short | 6h protnutí 2 průměrů ema/30/150/cross · none · target | 178 / +0,24 | 84 / +0,03 | +0,2 | +0,13 | 58 / +0,25 | +0,27 | 20 | 4 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/100/pullback · none · trail | 2776 / +0,10 | 1029 / -0,04 | -0,7 | +0,10 | 940 / +0,05 | +0,05 | 152 | 54 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/50/confirm · d50 · opp_stop | 1745 / +0,23 | 722 / -0,02 | -0,2 | -0,07 | 771 / +0,23 | +0,28 | 177 | 37 | ❌ |
| short | 1h protnutí 2 průměrů sma/30/100/pullback · d50 · trail | 2023 / +0,12 | 816 / -0,03 | -0,4 | +0,11 | 901 / -0,03 | +0,10 | 173 | 42 | ❌ |
| short | 6h protnutí 2 průměrů ema/30/100/cross · d50 · target | 155 / +0,26 | 65 / +0,11 | +0,8 | +0,13 | 60 / -0,14 | +0,18 | 21 | 3 | ❌ |
| short | 4h průraz s objemem 20/1.5 · none · target | 1021 / +0,10 | 423 / +0,09 | +1,6 | +0,08 | 391 / +0,02 | +0,18 | 61 | 21 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/200/cross · d50 · opp_stop | 459 / +0,61 | 211 / +0,25 | +1,1 | +0,12 | 251 / -0,36 | +0,63 | 129 | 10 | ❌ |
| short | 2h protnutí 2 průměrů sma/40/50/confirm · d50 · trail | 1240 / +0,14 | 500 / +0,03 | +0,4 | +0,16 | 583 / +0,01 | +0,18 | 90 | 26 | ❌ |
| short | 4h Donchian průraz 20 · d200 · target | 697 / +0,12 | 256 / +0,10 | +1,2 | +0,03 | 355 / +0,08 | +0,15 | 50 | 15 | ❌ |

## 5. Všechny kombinace, které splní kritéria (bez pořadí v IS) – kandidáti, ne důkaz

Splní je **239** z 33868 způsobilých kombinací. Čistou náhodou by to bylo řádově 25 (OOS i HOLDOUT nad p95 ≈ 0,25 %, k tomu t ≥ 2 a kladné IS). Kombinace v rámci rodiny jsou si podobné, takže skutečně nezávislých nálezů je méně.

| Směr | Kombinace | IS Ø R | OOS n / Ø R / t | HOLDOUT n / Ø R | Max. propad R | Obch./měs. | Ø % na obchod (OOS) |
|---|---|---|---|---|---|---|---|
| short | 6h Supertrend 10/3.0 · none · target | +0,03 | 201 / +0,36 / +4,1 | 172 / +0,24 | 50 | 10 | +1,85 |
| short | 6h Supertrend 10/3.0 · d50 · target | +0,09 | 80 / +0,52 / +3,9 | 92 / +0,24 | 24 | 4 | +3,45 |
| short | 2h Keltner průraz 2.5 · none · target | +0,04 | 430 / +0,20 / +3,5 | 418 / +0,14 | 54 | 22 | +0,44 |
| long | 1h Bollinger průraz 50/2.5 · none · opp_stop | +0,40 | 733 / +0,57 / +3,2 | 705 / +0,34 | 135 | 43 | +0,78 |
| long | 2h RSI momentum 60 · none · opp | +0,32 | 927 / +0,24 / +3,2 | 887 / +0,07 | 156 | 51 | +0,67 |
| long | 1h Bollinger průraz 50/2.5 · none · opp | +0,43 | 645 / +0,49 / +3,1 | 614 / +0,24 | 141 | 37 | +0,91 |
| long | 2h RSI momentum 55 · none · opp_stop | +0,24 | 1524 / +0,19 / +3,0 | 1464 / +0,05 | 226 | 86 | +0,37 |
| long | 1h Bollinger průraz 50/2.0 · none · opp | +0,37 | 906 / +0,37 / +3,0 | 852 / +0,12 | 182 | 50 | +0,67 |
| long | 2h RSI momentum 60 · none · opp_stop | +0,37 | 984 / +0,28 / +3,0 | 935 / +0,14 | 169 | 55 | +0,56 |
| short | 2h protnutí 2 průměrů sma/20/50/cross · none · target | +0,03 | 561 / +0,15 / +2,9 | 538 / +0,11 | 49 | 31 | +0,36 |
| long | 4h cena × průměr sma/20 · none · opp | +0,17 | 1518 / +0,12 / +2,9 | 1412 / +0,01 | 144 | 84 | +0,43 |
| long | 2h protnutí 2 průměrů ema/5/50/cross · none · trail | +0,18 | 797 / +0,22 / +2,9 | 786 / +0,09 | 111 | 43 | +0,50 |
| short | 1h protnutí 2 průměrů sma/50/100/cross · none · trail | +0,02 | 575 / +0,23 / +2,9 | 541 / +0,14 | 103 | 31 | +0,37 |
| long | 1h Bollinger průraz 50/2.0 · none · opp_stop | +0,36 | 1067 / +0,38 / +2,9 | 1024 / +0,16 | 201 | 61 | +0,48 |
| long | 6h Bollinger průraz 50/2.5 · d50 · target | +0,19 | 122 / +0,31 / +2,8 | 88 / +0,07 | 34 | 7 | +1,84 |
| long | 15m protnutí 2 průměrů ema/50/200/confirm · none · opp | +0,16 | 1469 / +0,40 / +2,8 | 1344 / +0,04 | 522 | 82 | +0,39 |
| long | 1h protnutí 2 průměrů sma/5/60/confirm · none · opp | +0,31 | 1542 / +0,24 / +2,8 | 1480 / +0,01 | 263 | 87 | +0,39 |
| long | 1h průraz s objemem 55/1.5 · none · opp | +0,78 | 553 / +0,57 / +2,7 | 479 / +0,44 | 195 | 29 | +0,95 |
| long | 1h protnutí 2 průměrů ema/10/50/cross · none · opp | +0,42 | 1391 / +0,27 / +2,7 | 1314 / +0,04 | 290 | 77 | +0,44 |
| long | 1h průraz s objemem 55/2.5 · none · opp | +1,06 | 434 / +0,65 / +2,7 | 386 / +0,52 | 125 | 22 | +1,18 |
| long | 2h MACD 19/39/9/signal · none · opp | +0,15 | 1528 / +0,12 / +2,7 | 1470 / +0,01 | 174 | 84 | +0,42 |
| long | 1h protnutí 2 průměrů sma/10/50/confirm · none · opp | +0,30 | 1347 / +0,26 / +2,7 | 1262 / +0,03 | 310 | 75 | +0,51 |
| short | 12h protnutí 2 průměrů ema/20/50/cross · none · target | +0,12 | 78 / +0,36 / +2,7 | 69 / +0,16 | 16 | 4 | +3,09 |
| long | 1h protnutí 2 průměrů ema/10/100/cross · none · opp_stop | +0,57 | 957 / +0,37 / +2,6 | 953 / +0,19 | 249 | 52 | +0,48 |
| long | 1h protnutí 2 průměrů sma/10/60/confirm · none · opp | +0,41 | 1199 / +0,29 / +2,6 | 1134 / +0,10 | 245 | 66 | +0,55 |
| long | 2h Bollinger průraz 50/2.0 · none · opp | +0,77 | 448 / +0,46 / +2,6 | 402 / +0,31 | 120 | 24 | +1,21 |
| short | 6h protnutí 2 průměrů ema/10/50/cross · none · target | +0,06 | 207 / +0,22 / +2,6 | 190 / +0,16 | 37 | 10 | +1,58 |
| long | 2h protnutí 2 průměrů sma/5/150/cross · none · trail | +0,20 | 434 / +0,28 / +2,6 | 412 / +0,25 | 60 | 23 | +0,69 |
| long | 12h MACD 19/39/9/signal · none · opp_stop | +0,89 | 240 / +0,76 / +2,6 | 214 / +0,17 | 44 | 13 | +3,72 |
| long | 2h protnutí 2 průměrů ema/10/50/cross · none · trail | +0,13 | 634 / +0,23 / +2,6 | 640 / +0,06 | 121 | 35 | +0,52 |
| long | 6h protnutí 2 průměrů ema/50/60/cross · none · target | +0,06 | 88 / +0,34 / +2,6 | 84 / +0,40 | 29 | 5 | +1,80 |
| long | 1h Donchian průraz 55 · none · opp | +0,75 | 607 / +0,51 / +2,6 | 539 / +0,33 | 205 | 32 | +0,81 |
| long | 2h protnutí 2 průměrů sma/5/60/cross · none · trail | +0,18 | 715 / +0,20 / +2,6 | 702 / +0,07 | 142 | 39 | +0,56 |
| long | 15m protnutí 2 průměrů ema/30/200/cross · none · opp | +0,03 | 1591 / +0,33 / +2,6 | 1541 / +0,01 | 547 | 91 | +0,26 |
| short | 4h Supertrend 20/3.0 · d50 · opp_stop | +0,17 | 116 / +0,47 / +2,6 | 162 / +0,23 | 48 | 7 | +1,41 |
| long | 6h Bollinger průraz 50/2.5 · none · target | +0,20 | 170 / +0,25 / +2,6 | 135 / +0,07 | 35 | 10 | +1,41 |
| long | 1h Bollinger průraz 50/2.5 · none · trail | +0,20 | 738 / +0,22 / +2,5 | 699 / +0,14 | 94 | 43 | +0,44 |
| long | 4h cena × průměr sma/20 · none · opp_stop | +0,21 | 1518 / +0,13 / +2,5 | 1412 / +0,03 | 177 | 84 | +0,36 |
| long | 6h RSI momentum 60 · none · opp | +0,77 | 310 / +0,52 / +2,5 | 286 / +0,17 | 77 | 17 | +2,28 |
| long | 2h protnutí 2 průměrů ema/10/30/cross · none · trail | +0,18 | 823 / +0,18 / +2,5 | 779 / +0,06 | 125 | 44 | +0,40 |

Podle rodiny a timeframu: protnutí 2 průměrů 2h long: 29; protnutí 2 průměrů 1h long: 23; protnutí 2 průměrů 6h long: 19; protnutí 2 průměrů 4h long: 18; Bollinger průraz 2h long: 12; Bollinger průraz 6h long: 11; Bollinger průraz 4h long: 9; protnutí 2 průměrů 1h short: 9; Bollinger průraz 1h long: 8; protnutí 2 průměrů 12h long: 8; Keltner průraz 6h long: 7; Bollinger průraz 12h long: 7; průraz s objemem 1h long: 6; Donchian průraz 6h long: 5; Donchian průraz 1h long: 5.

## Závěr

✅ **Předem stanovené pravidlo splnilo 1 kombinací:** long 2h protnutí 2 průměrů sma/5/200/pullback · none · opp. Další krok je papírové ověření vedle skeneru, ne ostré zapnutí.

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