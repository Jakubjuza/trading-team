# Atlas strategií – 15 rodin, 7 timeframů, poplatky MEXC (27. 10. 2026)

Otázka: je mezi běžnými pravidlovými strategiemi na kterémkoli timeframu něco, co po poplatcích MEXC vydělává spolehlivěji než náhoda? Metoda stanovená předem je v hlavičce `research/experiments/strategy_atlas.py`.

- **42 048 kombinací** (15 rodin, 248 variant × 7 timeframů × 3 filtry × 4 výstupy × long/short), 8 mincí.
- 12h: 5952 kombinací, 1144 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 15m: 5952 kombinací, 2830 s, data od BTC 01/2022, ETH 01/2022, SOL 01/2022, XRP 01/2022, ADA 01/2022, LINK 01/2022, AVAX 01/2022, DOGE 01/2022
- 1d: 5952 kombinací, 1114 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 1h: 5952 kombinací, 1160 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 2h: 5952 kombinací, 823 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 4h: 5952 kombinací, 784 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 6h: 5952 kombinací, 1176 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- sent_1d: 192 kombinací, 1070 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- sent_4h: 192 kombinací, 2 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- Poplatky na stranu: **MEXC futures taker 0,02 % + skluz 0,03 % = 0,05 % (rozhoduje)**; MEXC spot taker 0,08 %; maker 0 % (optimistická mez); 0,15 % (dřívější testy). Funding nezapočten. Poplatky MEXC podle [MEXC, 11/2025](https://www.mexc.com/ru-RU/crypto-pulse/article/mexc-trading-fees-complete-guide-39643).
- IS do 12/2023 (15M od 1/2022), OOS 1/2024–6/2025, HOLDOUT 7/2025–dnes. R = výsledek po poplatcích / riziko (vzdálenost stopu; bez stopu 2 ATR).

## 1. Mají rodiny strategií výhodu? (hlavní scénář poplatků)

„Nad náhodou“ = podíl kombinací, jejichž Ø R v daném období je nad mediánem jejich vlastních náhodných vstupů (bez výhody by to bylo ~50 %). „Obě nad p95“ = OOS i HOLDOUT nad 95. percentilem náhody (čistou náhodou ~0,25 %).

| Rodina | Směr | Kombinací | OOS > 0 | HOLDOUT > 0 | OOS nad náhodou | HOLDOUT nad náhodou | Obě nad p95 | Medián OOS R | Medián HOLDOUT R |
|---|---|---|---|---|---|---|---|---|---|
| Bollinger průraz | long | 336 | 81% | 74% | 94% | 91% | 54,5% | +0,25 | +0,15 |
| Bollinger průraz | short | 336 | 32% | 77% | 55% | 77% | 10,1% | -0,06 | +0,12 |
| Bollinger návrat | long | 336 | 21% | 25% | 17% | 31% | 0,0% | -0,11 | -0,09 |
| Bollinger návrat | short | 336 | 33% | 57% | 45% | 33% | 2,4% | -0,05 | +0,03 |
| svíčkové vzory | long | 168 | 50% | 35% | 61% | 46% | 0,6% | -0,00 | -0,03 |
| svíčkové vzory | short | 168 | 23% | 71% | 62% | 54% | 1,2% | -0,06 | +0,09 |
| Donchian průraz | long | 420 | 80% | 61% | 95% | 83% | 34,8% | +0,25 | +0,06 |
| Donchian průraz | short | 420 | 30% | 72% | 47% | 57% | 2,6% | -0,08 | +0,14 |
| strach a chamtivost | long | 192 | 35% | 21% | 27% | 20% | 1,0% | -0,16 | -0,36 |
| strach a chamtivost | short | 192 | 41% | 18% | 50% | 16% | 1,6% | +0,04 | -0,18 |
| Keltner průraz | long | 252 | 80% | 69% | 96% | 87% | 46,8% | +0,19 | +0,12 |
| Keltner průraz | short | 252 | 40% | 69% | 55% | 76% | 13,9% | -0,05 | +0,13 |
| protnutí 2 průměrů | long | 16128 | 66% | 52% | 70% | 69% | 9,7% | +0,16 | +0,01 |
| protnutí 2 průměrů | short | 16128 | 31% | 76% | 69% | 49% | 4,4% | -0,07 | +0,16 |
| MACD | long | 504 | 63% | 48% | 74% | 59% | 9,5% | +0,10 | -0,01 |
| MACD | short | 504 | 45% | 67% | 82% | 40% | 5,0% | -0,01 | +0,05 |
| cena × průměr | long | 840 | 54% | 49% | 55% | 51% | 4,2% | +0,02 | -0,00 |
| cena × průměr | short | 840 | 37% | 71% | 87% | 40% | 6,9% | -0,02 | +0,06 |
| momentum ROC | long | 336 | 56% | 47% | 58% | 55% | 4,2% | +0,02 | -0,01 |
| momentum ROC | short | 336 | 32% | 68% | 80% | 36% | 8,9% | -0,04 | +0,05 |
| RSI momentum | long | 252 | 62% | 58% | 74% | 71% | 12,3% | +0,06 | +0,02 |
| RSI momentum | short | 252 | 37% | 79% | 87% | 58% | 9,9% | -0,02 | +0,07 |
| RSI návrat | long | 336 | 23% | 17% | 23% | 26% | 0,0% | -0,09 | -0,12 |
| RSI návrat | short | 336 | 24% | 53% | 39% | 41% | 5,7% | -0,07 | +0,02 |
| Stochastic | long | 168 | 22% | 13% | 17% | 20% | 0,0% | -0,11 | -0,11 |
| Stochastic | short | 168 | 11% | 62% | 32% | 54% | 1,8% | -0,07 | +0,04 |
| Supertrend | long | 252 | 67% | 48% | 83% | 61% | 6,0% | +0,14 | -0,01 |
| Supertrend | short | 252 | 55% | 77% | 79% | 50% | 5,2% | +0,02 | +0,11 |
| sweep & reclaim | long | 168 | 34% | 9% | 19% | 11% | 0,0% | -0,10 | -0,15 |
| sweep & reclaim | short | 168 | 12% | 63% | 25% | 33% | 0,0% | -0,11 | +0,04 |
| průraz s objemem | long | 336 | 80% | 67% | 96% | 84% | 39,9% | +0,36 | +0,16 |
| průraz s objemem | short | 336 | 27% | 70% | 43% | 57% | 6,2% | -0,14 | +0,13 |

## 2. Podle timeframu (všechny rodiny dohromady)

| TF | Směr | OOS > 0 | HOLDOUT > 0 | OOS nad náhodou | HOLDOUT nad náhodou | Medián OOS R | Medián obchodů/měs. |
|---|---|---|---|---|---|---|---|
| 15m | long | 22% | 23% | 81% | 63% | -0,08 | 146 |
| 15m | short | 32% | 5% | 88% | 46% | -0,03 | 204 |
| 1h | long | 61% | 59% | 76% | 56% | +0,05 | 40 |
| 1h | short | 54% | 73% | 71% | 43% | +0,01 | 44 |
| 2h | long | 69% | 61% | 71% | 62% | +0,10 | 20 |
| 2h | short | 41% | 80% | 61% | 33% | -0,02 | 22 |
| 4h | long | 75% | 63% | 70% | 66% | +0,17 | 10 |
| 4h | short | 32% | 85% | 68% | 34% | -0,07 | 11 |
| 6h | long | 77% | 59% | 61% | 70% | +0,44 | 7 |
| 6h | short | 28% | 89% | 71% | 57% | -0,10 | 8 |
| 12h | long | 76% | 56% | 64% | 78% | +0,48 | 3 |
| 12h | short | 22% | 92% | 65% | 62% | -0,18 | 4 |
| 1d | long | 65% | 35% | 57% | 65% | +0,30 | 2 |
| 1d | short | 12% | 90% | 52% | 67% | -0,28 | 2 |

## 3. Kolik dělají poplatky

Podíl všech kombinací s kladným Ø R v OOS a v HOLDOUT podle výše poplatků:

| Poplatky na stranu | OOS > 0 long | OOS > 0 short | HOLDOUT > 0 long | HOLDOUT > 0 short | Projde pravidlem (ze všech) |
|---|---|---|---|---|---|
| 0 % (maker, optimisticky) | 76% | 47% | 64% | 91% | 1000 z 33872 |
| 0,05 % (MEXC futures taker) | 64% | 31% | 51% | 74% | 226 z 33872 |
| 0,08 % (MEXC spot taker) | 60% | 23% | 45% | 67% | 156 z 33872 |
| 0,15 % (dřívější testy) | 54% | 14% | 37% | 57% | 64 z 33872 |

## 4. Výběr podle předem stanoveného pravidla (50 nejlepších podle IS t-statistiky na směr)

| Směr | Kombinace | IS n / Ø R | OOS n / Ø R | OOS t | Náhoda OOS p95 | HOLDOUT n / Ø R | Náhoda HOLD p95 | Max. propad R | Obch./měs. | Prošlo |
|---|---|---|---|---|---|---|---|---|---|---|
| long | 2h MACD 19/39/9/signal · d50 · opp | 2019 / +0,31 | 635 / +0,07 | +1,1 | +0,06 | 460 / +0,12 | +0,15 | 64 | 35 | ❌ |
| long | 1h protnutí 2 průměrů sma/30/200/confirm · none · opp | 1178 / +1,67 | 420 / +0,61 | +1,9 | +1,06 | 385 / +0,07 | +0,27 | 245 | 22 | ❌ |
| long | 12h MACD 5/35/5/signal · none · opp | 1591 / +0,32 | 573 / +0,16 | +2,4 | +0,28 | 547 / +0,01 | +0,09 | 73 | 30 | ❌ |
| long | 1h protnutí 2 průměrů sma/40/200/confirm · none · opp | 1071 / +1,82 | 379 / +0,83 | +2,1 | +1,41 | 337 / +0,09 | +0,45 | 246 | 20 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/30/cross · d50 · opp | 2795 / +0,39 | 867 / +0,06 | +0,8 | +0,03 | 618 / +0,10 | +0,34 | 107 | 48 | ❌ |
| long | 6h MACD 12/26/9/signal · none · opp | 1904 / +0,35 | 660 / +0,24 | +2,9 | +0,28 | 678 / -0,02 | +0,01 | 123 | 36 | ❌ |
| long | 6h MACD 19/39/9/signal · none · opp | 1450 / +0,54 | 506 / +0,26 | +2,5 | +0,45 | 515 / +0,03 | +0,07 | 107 | 28 | ❌ |
| long | 4h MACD 5/35/5/signal · d50 · opp | 2312 / +0,18 | 748 / +0,04 | +1,0 | +0,01 | 508 / +0,08 | +0,13 | 43 | 40 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/200/confirm · none · opp | 1773 / +1,05 | 609 / +0,47 | +2,1 | +0,74 | 581 / +0,20 | +0,03 | 253 | 33 | ❌ |
| long | 12h MACD 5/35/5/signal · none · opp_stop | 1591 / +0,41 | 573 / +0,19 | +2,3 | +0,17 | 547 / +0,02 | +0,11 | 93 | 30 | ❌ |
| long | 1h protnutí 2 průměrů sma/30/200/confirm · d50 · opp | 740 / +2,10 | 254 / +0,60 | +1,2 | +1,19 | 178 / +0,87 | +1,33 | 117 | 13 | ❌ |
| long | 1h protnutí 2 průměrů ema/50/60/confirm · none · opp | 1682 / +1,28 | 596 / +0,59 | +2,4 | +0,94 | 589 / +0,07 | -0,10 | 288 | 32 | ❌ |
| long | 1h protnutí 2 průměrů ema/50/200/confirm · none · opp | 1029 / +1,86 | 357 / +0,69 | +2,0 | +1,10 | 337 / +0,00 | +0,06 | 295 | 19 | ❌ |
| long | 2h protnutí 2 průměrů sma/20/200/confirm · none · opp | 633 / +2,38 | 229 / +1,69 | +2,2 | +2,38 | 208 / -0,23 | -0,08 | 192 | 12 | ❌ |
| long | 1h protnutí 2 průměrů sma/20/200/confirm · none · opp | 1381 / +1,36 | 479 / +0,52 | +1,8 | +0,98 | 447 / +0,03 | +0,12 | 289 | 26 | ❌ |
| long | 1h protnutí 2 průměrů ema/40/100/confirm · none · opp | 1515 / +1,24 | 528 / +0,54 | +2,0 | +0,95 | 513 / +0,13 | +0,17 | 291 | 29 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/200/confirm · none · opp | 1075 / +1,58 | 361 / +1,05 | +2,5 | +1,77 | 362 / +0,10 | -0,11 | 180 | 20 | ❌ |
| long | 1h protnutí 2 průměrů ema/40/200/confirm · none · opp | 1125 / +1,64 | 400 / +0,65 | +2,1 | +1,14 | 369 / +0,07 | +0,25 | 283 | 21 | ❌ |
| long | 1h protnutí 2 průměrů sma/40/200/confirm · d50 · opp | 681 / +2,26 | 228 / +0,75 | +1,3 | +0,97 | 157 / +1,40 | +1,69 | 105 | 12 | ❌ |
| long | 4h protnutí 2 průměrů sma/10/100/confirm · none · opp | 558 / +1,95 | 209 / +1,51 | +2,2 | +2,48 | 194 / -0,07 | -0,48 | 123 | 11 | ❌ |
| long | 4h protnutí 2 průměrů sma/10/100/cross · none · opp | 596 / +1,83 | 216 / +1,48 | +2,2 | +2,30 | 203 / -0,06 | -0,39 | 121 | 11 | ❌ |
| long | 1h protnutí 2 průměrů ema/30/100/confirm · none · opp | 1709 / +1,08 | 594 / +0,48 | +2,1 | +0,88 | 590 / +0,13 | +0,07 | 270 | 33 | ❌ |
| long | 2h protnutí 2 průměrů ema/10/30/confirm · none · opp | 2543 / +0,51 | 916 / +0,30 | +2,5 | +0,43 | 895 / +0,07 | +0,06 | 191 | 49 | ❌ |
| long | 4h protnutí 2 průměrů sma/5/30/cross · none · opp | 1771 / +0,57 | 639 / +0,26 | +2,4 | +0,41 | 610 / +0,02 | -0,04 | 137 | 34 | ❌ |
| long | 2h protnutí 2 průměrů ema/40/150/confirm · none · opp | 589 / +2,55 | 225 / +1,68 | +2,0 | +1,64 | 198 / +0,08 | -0,35 | 142 | 11 | ❌ |
| long | 2h protnutí 2 průměrů ema/10/30/cross · none · opp | 2538 / +0,51 | 916 / +0,30 | +2,5 | +0,34 | 895 / +0,07 | -0,00 | 191 | 49 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/60/cross · none · opp | 2311 / +0,65 | 813 / +0,33 | +2,5 | +0,57 | 793 / +0,04 | +0,02 | 210 | 44 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/150/confirm · none · opp | 2011 / +1,01 | 696 / +0,43 | +2,2 | +0,79 | 693 / +0,08 | -0,08 | 302 | 38 | ❌ |
| long | 2h protnutí 2 průměrů sma/10/200/confirm · none · opp | 851 / +1,89 | 292 / +1,27 | +2,4 | +1,81 | 283 / -0,02 | -0,22 | 194 | 16 | ❌ |
| long | 1h protnutí 2 průměrů sma/20/150/confirm · none · opp | 1581 / +1,23 | 530 / +0,61 | +2,2 | +0,66 | 534 / +0,10 | +0,17 | 288 | 30 | ❌ |
| long | 4h MACD 19/39/9/signal · none · opp | 2222 / +0,35 | 767 / +0,24 | +3,1 | +0,27 | 769 / -0,02 | +0,01 | 152 | 42 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/30/confirm · d50 · opp | 2938 / +0,36 | 963 / +0,08 | +1,1 | +0,02 | 684 / +0,16 | +0,28 | 124 | 52 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/200/pullback · none · opp | 832 / +1,73 | 277 / +1,34 | +2,1 | +1,87 | 258 / +0,16 | -0,10 | 139 | 15 | ❌ |
| long | 2h MACD 12/26/9/zero · none · opp | 2512 / +0,50 | 916 / +0,28 | +2,4 | +0,37 | 875 / +0,07 | -0,02 | 187 | 48 | ❌ |
| long | 4h protnutí 2 průměrů sma/10/60/confirm · none · opp | 837 / +1,26 | 298 / +0,77 | +2,0 | +1,25 | 297 / +0,00 | -0,12 | 110 | 16 | ❌ |
| long | 1h protnutí 2 průměrů ema/40/150/confirm · none · opp | 1297 / +1,37 | 464 / +0,55 | +1,8 | +1,10 | 419 / +0,01 | -0,10 | 279 | 25 | ❌ |
| long | 4h protnutí 2 průměrů sma/5/30/confirm · none · opp | 1686 / +0,59 | 600 / +0,28 | +2,5 | +0,39 | 576 / +0,03 | +0,02 | 134 | 32 | ❌ |
| long | 1h protnutí 2 průměrů sma/50/200/confirm · none · opp | 1028 / +1,82 | 346 / +0,71 | +1,8 | +1,02 | 320 / +0,20 | +0,47 | 236 | 19 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/60/confirm · none · opp | 2201 / +0,67 | 775 / +0,33 | +2,4 | +0,60 | 749 / +0,05 | +0,01 | 202 | 42 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/50/cross · none · opp | 2572 / +0,56 | 905 / +0,26 | +2,5 | +0,37 | 873 / +0,04 | +0,03 | 213 | 49 | ❌ |
| long | 2h protnutí 2 průměrů sma/10/60/cross · none · opp | 1777 / +0,82 | 631 / +0,40 | +2,3 | +0,63 | 623 / +0,00 | -0,03 | 210 | 34 | ❌ |
| long | 2h protnutí 2 průměrů sma/10/60/confirm · none · opp | 1699 / +0,85 | 592 / +0,44 | +2,4 | +0,77 | 587 / +0,02 | -0,03 | 201 | 32 | ❌ |
| long | 4h protnutí 2 průměrů ema/20/30/cross · none · opp | 925 / +1,15 | 338 / +0,69 | +2,0 | +1,09 | 320 / -0,03 | -0,15 | 139 | 18 | ❌ |
| long | 12h MACD 19/39/9/signal · none · opp | 698 / +0,78 | 240 / +0,65 | +2,9 | +0,75 | 223 / +0,09 | -0,09 | 49 | 13 | ❌ |
| long | 1h protnutí 2 průměrů ema/50/60/cross · none · opp | 1621 / +1,27 | 582 / +0,56 | +2,2 | +1,01 | 582 / +0,08 | +0,25 | 288 | 31 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/50/confirm · none · opp | 2445 / +0,59 | 859 / +0,27 | +2,5 | +0,31 | 834 / +0,05 | +0,09 | 210 | 47 | ❌ |
| long | 4h momentum ROC 20 · none · opp | 3915 / +0,23 | 1370 / +0,08 | +1,7 | +0,16 | 1224 / -0,00 | +0,03 | 171 | 73 | ❌ |
| long | 4h protnutí 2 průměrů ema/10/60/confirm · none · opp | 846 / +1,33 | 313 / +0,70 | +2,0 | +1,30 | 294 / +0,07 | -0,24 | 126 | 16 | ❌ |
| long | 4h protnutí 2 průměrů ema/20/30/confirm · none · opp | 929 / +1,14 | 338 / +0,69 | +2,0 | +1,24 | 320 / -0,03 | -0,07 | 139 | 18 | ❌ |
| long | 4h protnutí 2 průměrů ema/10/60/cross · none · opp | 844 / +1,34 | 313 / +0,70 | +2,0 | +1,50 | 294 / +0,07 | -0,18 | 126 | 16 | ❌ |
| short | 4h průraz s objemem 20/2.5 · none · target | 549 / +0,24 | 261 / +0,19 | +2,6 | +0,07 | 244 / +0,13 | +0,14 | 49 | 12 | ❌ |
| short | 6h MACD 19/39/9/signal · d50 · opp_stop | 585 / +0,30 | 224 / +0,12 | +1,2 | +0,06 | 308 / +0,15 | +0,20 | 45 | 13 | ❌ |
| short | 4h průraz s objemem 55/2.5 · d50 · target | 270 / +0,28 | 137 / +0,00 | +0,0 | -0,00 | 158 / +0,17 | +0,31 | 23 | 6 | ❌ |
| short | 6h MACD 12/26/9/signal · d50 · opp_stop | 755 / +0,23 | 310 / +0,03 | +0,3 | +0,02 | 401 / +0,00 | +0,14 | 70 | 16 | ❌ |
| short | 4h průraz s objemem 20/1.5 · d200 · target | 526 / +0,19 | 188 / -0,01 | -0,1 | +0,05 | 310 / +0,07 | +0,20 | 44 | 12 | ❌ |
| short | 4h průraz s objemem 55/2.5 · none · target | 363 / +0,23 | 179 / +0,08 | +0,9 | +0,13 | 191 / +0,14 | +0,20 | 36 | 8 | ❌ |
| short | 4h průraz s objemem 20/2.5 · d200 · target | 283 / +0,26 | 115 / +0,07 | +0,6 | +0,03 | 181 / +0,07 | +0,21 | 38 | 7 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/60/pullback · d50 · trail | 1481 / +0,18 | 597 / -0,11 | -1,7 | +0,07 | 628 / +0,08 | +0,12 | 121 | 30 | ❌ |
| short | 4h průraz s objemem 20/2.5 · d50 · target | 324 / +0,23 | 169 / +0,02 | +0,2 | +0,00 | 179 / +0,12 | +0,27 | 32 | 8 | ❌ |
| short | 4h průraz s objemem 55/2.5 · d200 · target | 219 / +0,28 | 91 / +0,02 | +0,1 | +0,07 | 154 / +0,13 | +0,26 | 26 | 5 | ❌ |
| short | 2h Bollinger průraz 50/2.5 · d50 · target | 725 / +0,15 | 291 / +0,11 | +1,5 | +0,05 | 333 / +0,04 | +0,13 | 44 | 15 | ❌ |
| short | 4h MACD 19/39/9/signal · d50 · opp_stop | 916 / +0,20 | 362 / +0,07 | +0,9 | -0,00 | 468 / -0,02 | +0,25 | 82 | 20 | ❌ |
| short | 6h MACD 19/39/9/signal · d50 · opp | 585 / +0,20 | 224 / +0,07 | +0,8 | +0,10 | 308 / +0,05 | +0,27 | 45 | 13 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/100/confirm · d50 · trail | 2117 / +0,13 | 869 / -0,02 | -0,3 | +0,09 | 931 / +0,06 | +0,15 | 110 | 44 | ❌ |
| short | 6h MACD 19/39/9/signal · d200 · opp_stop | 620 / +0,24 | 178 / +0,04 | +0,4 | +0,11 | 363 / +0,12 | +0,20 | 57 | 13 | ❌ |
| short | 1h protnutí 2 průměrů sma/40/50/pullback · d50 · trail | 1678 / +0,15 | 626 / -0,07 | -1,0 | +0,10 | 689 / +0,16 | +0,09 | 112 | 34 | ❌ |
| short | 6h protnutí 2 průměrů ema/50/100/cross · none · target | 178 / +0,27 | 74 / -0,16 | -1,2 | +0,16 | 57 / +0,28 | +0,22 | 26 | 3 | ❌ |
| short | 1h Bollinger průraz 50/2.0 · d50 · trail | 1557 / +0,16 | 656 / +0,07 | +0,9 | +0,09 | 747 / +0,06 | +0,14 | 102 | 33 | ❌ |
| short | 2h protnutí 2 průměrů ema/30/200/cross · none · target | 482 / +0,17 | 202 / +0,21 | +2,5 | +0,17 | 175 / +0,04 | +0,16 | 30 | 10 | ❌ |
| short | 1h protnutí 2 průměrů ema/20/100/cross · d50 · opp_stop | 785 / +0,46 | 327 / +0,15 | +0,9 | +0,04 | 395 / +0,12 | +0,58 | 116 | 17 | ❌ |
| short | 12h protnutí 2 průměrů ema/5/150/cross · none · trail | 162 / +0,37 | 86 / -0,24 | -2,2 | +0,06 | 53 / +1,20 | +0,62 | 33 | 3 | ❌ |
| short | 4h Bollinger průraz 50/2.5 · d200 · target | 302 / +0,21 | 98 / +0,16 | +1,3 | +0,07 | 161 / +0,25 | +0,21 | 23 | 6 | ❌ |
| short | 1h protnutí 2 průměrů sma/30/50/pullback · d50 · trail | 1797 / +0,14 | 706 / +0,04 | +0,6 | +0,09 | 798 / +0,15 | +0,11 | 77 | 37 | ❌ |
| short | 1h Bollinger průraz 50/2.0 · d200 · trail | 1419 / +0,15 | 469 / +0,07 | +0,9 | +0,08 | 803 / +0,03 | +0,14 | 101 | 30 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/60/confirm · d50 · trail | 2279 / +0,12 | 902 / -0,01 | -0,2 | +0,06 | 959 / +0,13 | +0,09 | 85 | 47 | ❌ |
| short | 2h protnutí 2 průměrů sma/20/30/pullback · d50 · trail | 1045 / +0,17 | 373 / -0,02 | -0,2 | +0,10 | 423 / +0,15 | +0,27 | 58 | 21 | ❌ |
| short | 1h protnutí 2 průměrů ema/50/60/confirm · d50 · trail | 2341 / +0,12 | 963 / +0,02 | +0,3 | +0,07 | 1105 / +0,07 | +0,11 | 108 | 50 | ❌ |
| short | 6h MACD 12/26/9/signal · d200 · opp_stop | 790 / +0,17 | 244 / +0,04 | +0,5 | +0,02 | 467 / +0,03 | +0,13 | 69 | 17 | ❌ |
| short | 1h cena × průměr ema/50 · d50 · trail | 2984 / +0,10 | 1190 / +0,04 | +0,7 | +0,08 | 1396 / +0,10 | +0,09 | 114 | 63 | ❌ |
| short | 2h protnutí 2 průměrů ema/40/150/cross · none · target | 496 / +0,15 | 203 / +0,09 | +1,1 | +0,11 | 188 / -0,02 | +0,19 | 38 | 10 | ❌ |
| short | 6h protnutí 2 průměrů ema/20/200/cross · none · target | 178 / +0,25 | 91 / -0,06 | -0,5 | +0,14 | 64 / +0,04 | +0,27 | 25 | 4 | ❌ |
| short | 2h protnutí 2 průměrů sma/5/60/pullback · d50 · trail | 1551 / +0,13 | 637 / -0,01 | -0,1 | +0,14 | 731 / +0,01 | +0,22 | 124 | 33 | ❌ |
| short | 2h protnutí 2 průměrů sma/40/50/cross · d50 · opp_stop | 995 / +0,24 | 407 / -0,01 | -0,1 | +0,01 | 444 / +0,24 | +0,21 | 87 | 21 | ❌ |
| short | 6h MACD 12/26/9/signal · d50 · opp | 755 / +0,14 | 310 / +0,00 | +0,0 | -0,02 | 401 / -0,02 | +0,02 | 67 | 16 | ❌ |
| short | 2h protnutí 2 průměrů sma/10/60/pullback · d50 · opp | 786 / +0,25 | 312 / -0,10 | -1,0 | -0,08 | 342 / +0,15 | +0,54 | 100 | 16 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/100/pullback · d50 · trail | 1638 / +0,14 | 673 / -0,10 | -1,6 | +0,08 | 690 / +0,03 | +0,07 | 148 | 34 | ❌ |
| short | 6h Supertrend 20/3.0 · d200 · opp | 198 / +0,42 | 70 / +0,21 | +1,3 | -0,34 | 117 / +0,20 | +0,69 | 48 | 4 | ❌ |
| short | 1h protnutí 2 průměrů ema/50/60/confirm · d50 · opp | 915 / +0,35 | 385 / -0,13 | -0,9 | +0,03 | 430 / +0,19 | +0,61 | 169 | 19 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/150/cross · d50 · opp_stop | 551 / +0,52 | 233 / +0,14 | +0,7 | -0,04 | 263 / -0,08 | +0,76 | 116 | 12 | ❌ |
| short | 12h MACD 5/35/5/signal · d200 · opp_stop | 652 / +0,13 | 198 / +0,05 | +0,7 | +0,04 | 386 / +0,08 | +0,08 | 39 | 14 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/60/pullback · d50 · trail | 2032 / +0,12 | 849 / -0,02 | -0,3 | +0,09 | 919 / +0,07 | +0,11 | 106 | 43 | ❌ |
| short | 6h protnutí 2 průměrů ema/30/150/cross · none · target | 178 / +0,24 | 84 / +0,03 | +0,2 | +0,16 | 58 / +0,25 | +0,14 | 20 | 4 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/100/pullback · none · trail | 2776 / +0,10 | 1029 / -0,04 | -0,7 | +0,09 | 964 / +0,08 | +0,07 | 152 | 54 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/50/confirm · d50 · opp_stop | 1745 / +0,23 | 722 / -0,02 | -0,2 | +0,01 | 778 / +0,31 | +0,29 | 177 | 37 | ❌ |
| short | 1h protnutí 2 průměrů sma/30/100/pullback · d50 · trail | 2023 / +0,12 | 816 / -0,03 | -0,4 | +0,10 | 927 / -0,01 | +0,12 | 173 | 42 | ❌ |
| short | 6h protnutí 2 průměrů ema/30/100/cross · d50 · target | 155 / +0,26 | 65 / +0,11 | +0,8 | +0,10 | 60 / -0,14 | +0,23 | 21 | 3 | ❌ |
| short | 4h průraz s objemem 20/1.5 · none · target | 1021 / +0,10 | 423 / +0,09 | +1,6 | +0,07 | 407 / +0,07 | +0,11 | 61 | 21 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/200/cross · d50 · opp_stop | 459 / +0,61 | 211 / +0,25 | +1,1 | -0,13 | 251 / -0,33 | +0,47 | 129 | 10 | ❌ |
| short | 2h protnutí 2 průměrů sma/40/50/confirm · d50 · trail | 1240 / +0,14 | 500 / +0,03 | +0,4 | +0,10 | 596 / +0,02 | +0,23 | 90 | 26 | ❌ |
| short | 4h Donchian průraz 20 · d200 · target | 697 / +0,12 | 256 / +0,10 | +1,2 | +0,02 | 372 / +0,13 | +0,21 | 50 | 15 | ❌ |

## 5. Všechny kombinace, které splní kritéria (bez pořadí v IS) – kandidáti, ne důkaz

Splní je **226** z 33872 způsobilých kombinací. Čistou náhodou by to bylo řádově 25 (OOS i HOLDOUT nad p95 ≈ 0,25 %, k tomu t ≥ 2 a kladné IS). Kombinace v rámci rodiny jsou si podobné, takže skutečně nezávislých nálezů je méně.

| Směr | Kombinace | IS Ø R | OOS n / Ø R / t | HOLDOUT n / Ø R | Max. propad R | Obch./měs. | Ø % na obchod (OOS) |
|---|---|---|---|---|---|---|---|
| short | 6h Supertrend 10/3.0 · none · target | +0,03 | 201 / +0,36 / +4,1 | 172 / +0,25 | 50 | 10 | +1,85 |
| short | 6h Supertrend 10/3.0 · d200 · target | +0,14 | 71 / +0,58 / +4,1 | 111 / +0,24 | 19 | 4 | +3,68 |
| short | 6h Supertrend 10/3.0 · d50 · target | +0,09 | 80 / +0,52 / +3,9 | 92 / +0,25 | 24 | 4 | +3,45 |
| short | 2h Keltner průraz 2.5 · none · target | +0,04 | 430 / +0,20 / +3,5 | 428 / +0,13 | 54 | 22 | +0,44 |
| long | 1h protnutí 2 průměrů sma/50/60/confirm · none · opp | +0,37 | 1053 / +0,41 / +3,2 | 1028 / +0,05 | 280 | 60 | +0,79 |
| long | 1h Bollinger průraz 50/2.5 · none · opp_stop | +0,40 | 733 / +0,57 / +3,2 | 709 / +0,33 | 135 | 43 | +0,78 |
| short | 2h protnutí 2 průměrů ema/20/200/cross · none · target | +0,06 | 234 / +0,24 / +3,1 | 207 / +0,12 | 25 | 11 | +0,72 |
| long | 1h Bollinger průraz 50/2.5 · none · opp | +0,43 | 645 / +0,49 / +3,1 | 617 / +0,23 | 141 | 37 | +0,91 |
| short | 6h protnutí 2 průměrů ema/50/100/pullback · none · target | +0,01 | 177 / +0,28 / +3,1 | 168 / +0,21 | 41 | 8 | +1,83 |
| long | 2h RSI momentum 55 · none · opp_stop | +0,24 | 1524 / +0,19 / +3,0 | 1486 / +0,04 | 226 | 86 | +0,37 |
| long | 2h RSI momentum 60 · none · opp_stop | +0,37 | 984 / +0,28 / +3,0 | 947 / +0,12 | 169 | 55 | +0,56 |
| short | 2h protnutí 2 průměrů sma/20/50/cross · none · target | +0,03 | 561 / +0,15 / +2,9 | 543 / +0,12 | 49 | 31 | +0,36 |
| long | 4h cena × průměr sma/20 · none · opp | +0,17 | 1518 / +0,12 / +2,9 | 1433 / +0,01 | 144 | 84 | +0,43 |
| long | 2h protnutí 2 průměrů ema/5/50/cross · none · trail | +0,18 | 797 / +0,22 / +2,9 | 796 / +0,08 | 111 | 43 | +0,50 |
| short | 1h protnutí 2 průměrů sma/50/100/cross · none · trail | +0,02 | 575 / +0,23 / +2,9 | 546 / +0,15 | 103 | 31 | +0,37 |
| long | 1h Bollinger průraz 50/2.0 · none · opp_stop | +0,36 | 1067 / +0,38 / +2,9 | 1032 / +0,15 | 201 | 60 | +0,48 |
| long | 6h Bollinger průraz 50/2.5 · d50 · target | +0,19 | 122 / +0,31 / +2,8 | 88 / +0,07 | 34 | 7 | +1,84 |
| long | 15m protnutí 2 průměrů ema/50/200/confirm · none · opp | +0,16 | 1469 / +0,40 / +2,8 | 1356 / +0,02 | 522 | 82 | +0,39 |
| long | 1h průraz s objemem 55/1.5 · none · opp | +0,78 | 553 / +0,57 / +2,7 | 482 / +0,43 | 195 | 29 | +0,95 |
| long | 1h průraz s objemem 55/2.5 · none · opp | +1,06 | 434 / +0,65 / +2,7 | 386 / +0,52 | 125 | 22 | +1,18 |
| long | 2h MACD 19/39/9/signal · none · opp | +0,15 | 1528 / +0,12 / +2,7 | 1484 / +0,01 | 174 | 84 | +0,42 |
| long | 1h protnutí 2 průměrů sma/10/50/cross · none · opp | +0,28 | 1410 / +0,25 / +2,7 | 1368 / +0,00 | 321 | 79 | +0,49 |
| short | 6h protnutí 2 průměrů ema/50/150/pullback · none · target | +0,01 | 174 / +0,24 / +2,6 | 179 / +0,18 | 41 | 9 | +1,56 |
| long | 1h protnutí 2 průměrů ema/10/100/cross · none · opp_stop | +0,57 | 957 / +0,37 / +2,6 | 957 / +0,19 | 249 | 52 | +0,48 |
| long | 1h protnutí 2 průměrů sma/10/60/confirm · none · opp | +0,41 | 1199 / +0,29 / +2,6 | 1151 / +0,09 | 245 | 66 | +0,55 |
| long | 2h Bollinger průraz 50/2.0 · none · opp | +0,77 | 448 / +0,46 / +2,6 | 406 / +0,29 | 120 | 24 | +1,21 |
| long | 2h protnutí 2 průměrů sma/5/150/cross · none · trail | +0,20 | 434 / +0,28 / +2,6 | 413 / +0,25 | 60 | 23 | +0,69 |
| long | 6h protnutí 2 průměrů ema/50/60/cross · none · target | +0,06 | 88 / +0,34 / +2,6 | 84 / +0,40 | 29 | 5 | +1,80 |
| long | 1h Donchian průraz 55 · none · opp | +0,75 | 607 / +0,51 / +2,6 | 542 / +0,32 | 205 | 32 | +0,81 |
| long | 6h Bollinger průraz 50/2.5 · none · target | +0,20 | 170 / +0,25 / +2,6 | 135 / +0,07 | 35 | 10 | +1,41 |
| long | 1h protnutí 2 průměrů ema/10/60/cross · none · opp | +0,51 | 1266 / +0,27 / +2,6 | 1217 / +0,02 | 303 | 69 | +0,49 |
| long | 1h Bollinger průraz 50/2.5 · none · trail | +0,20 | 738 / +0,22 / +2,5 | 703 / +0,13 | 94 | 43 | +0,44 |
| long | 1h Bollinger průraz 50/2.0 · none · trail | +0,16 | 1057 / +0,17 / +2,5 | 1001 / +0,06 | 133 | 60 | +0,35 |
| long | 4h cena × průměr sma/20 · none · opp_stop | +0,21 | 1518 / +0,13 / +2,5 | 1433 / +0,03 | 177 | 84 | +0,36 |
| long | 6h RSI momentum 60 · none · opp | +0,77 | 310 / +0,52 / +2,5 | 286 / +0,17 | 77 | 17 | +2,28 |
| long | 1h protnutí 2 průměrů ema/10/100/confirm · none · opp_stop | +0,64 | 1237 / +0,36 / +2,5 | 1248 / +0,14 | 343 | 70 | +0,47 |
| long | 6h Bollinger průraz 20/2.0 · none · opp | +0,61 | 322 / +0,42 / +2,5 | 269 / +0,28 | 60 | 17 | +1,69 |
| short | 1h protnutí 2 průměrů sma/40/50/cross · none · trail | +0,02 | 1251 / +0,13 / +2,5 | 1208 / +0,07 | 119 | 70 | +0,09 |
| long | 2h protnutí 2 průměrů ema/5/50/cross · none · opp_stop | +0,54 | 948 / +0,38 / +2,5 | 959 / +0,06 | 236 | 52 | +0,71 |
| long | 6h RSI momentum 60 · none · opp_stop | +0,87 | 325 / +0,64 / +2,5 | 305 / +0,25 | 93 | 18 | +2,13 |

Podle rodiny a timeframu: protnutí 2 průměrů 2h long: 22; protnutí 2 průměrů 1h long: 21; protnutí 2 průměrů 6h long: 19; protnutí 2 průměrů 4h long: 19; Bollinger průraz 2h long: 12; Bollinger průraz 6h long: 11; protnutí 2 průměrů 12h long: 10; Bollinger průraz 4h long: 9; Bollinger průraz 1h long: 8; Keltner průraz 6h long: 7; Donchian průraz 1h long: 6; průraz s objemem 1h long: 6; Bollinger průraz 12h long: 6; protnutí 2 průměrů 1h short: 5; protnutí 2 průměrů 15m long: 5.

## Závěr

❌ **Předem stanovené pravidlo nesplnila žádná kombinace.**

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