# Atlas strategií – 15 rodin, 7 timeframů, poplatky MEXC (27. 10. 2026)

Otázka: je mezi běžnými pravidlovými strategiemi na kterémkoli timeframu něco, co po poplatcích MEXC vydělává spolehlivěji než náhoda? Metoda stanovená předem je v hlavičce `research/experiments/strategy_atlas.py`.

- **42 048 kombinací** (15 rodin, 248 variant × 7 timeframů × 3 filtry × 4 výstupy × long/short), 8 mincí.
- 12h: 5952 kombinací, 1158 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 15m: 5952 kombinací, 3752 s, data od BTC 01/2022, ETH 01/2022, SOL 01/2022, XRP 01/2022, ADA 01/2022, LINK 01/2022, AVAX 01/2022, DOGE 01/2022
- 1d: 5952 kombinací, 1060 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 1h: 5952 kombinací, 1101 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 2h: 5952 kombinací, 1090 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 4h: 5952 kombinací, 824 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 6h: 5952 kombinací, 1155 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- sent_1d: 192 kombinací, 1054 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- sent_4h: 192 kombinací, 1 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- Poplatky na stranu: **MEXC futures taker 0,02 % + skluz 0,03 % = 0,05 % (rozhoduje)**; MEXC spot taker 0,08 %; maker 0 % (optimistická mez); 0,15 % (dřívější testy). Funding nezapočten. Poplatky MEXC podle [MEXC, 11/2025](https://www.mexc.com/ru-RU/crypto-pulse/article/mexc-trading-fees-complete-guide-39643).
- IS do 12/2023 (15M od 1/2022), OOS 1/2024–6/2025, HOLDOUT 7/2025–dnes. R = výsledek po poplatcích / riziko (vzdálenost stopu; bez stopu 2 ATR).

## 1. Mají rodiny strategií výhodu? (hlavní scénář poplatků)

„Nad náhodou“ = podíl kombinací, jejichž Ø R v daném období je nad mediánem jejich vlastních náhodných vstupů (bez výhody by to bylo ~50 %). „Obě nad p95“ = OOS i HOLDOUT nad 95. percentilem náhody (čistou náhodou ~0,25 %).

| Rodina | Směr | Kombinací | OOS > 0 | HOLDOUT > 0 | OOS nad náhodou | HOLDOUT nad náhodou | Obě nad p95 | Medián OOS R | Medián HOLDOUT R |
|---|---|---|---|---|---|---|---|---|---|
| Bollinger průraz | long | 336 | 81% | 74% | 95% | 89% | 54,2% | +0,25 | +0,16 |
| Bollinger průraz | short | 336 | 32% | 67% | 56% | 77% | 10,4% | -0,06 | +0,06 |
| Bollinger návrat | long | 336 | 21% | 28% | 19% | 34% | 0,3% | -0,11 | -0,08 |
| Bollinger návrat | short | 336 | 33% | 52% | 44% | 46% | 4,2% | -0,05 | +0,01 |
| svíčkové vzory | long | 168 | 50% | 41% | 60% | 46% | 3,0% | -0,00 | -0,02 |
| svíčkové vzory | short | 168 | 23% | 58% | 57% | 55% | 3,0% | -0,06 | +0,03 |
| Donchian průraz | long | 420 | 80% | 62% | 95% | 84% | 30,0% | +0,25 | +0,07 |
| Donchian průraz | short | 420 | 30% | 63% | 49% | 48% | 1,7% | -0,08 | +0,04 |
| strach a chamtivost | long | 192 | 35% | 25% | 26% | 20% | 0,5% | -0,16 | -0,32 |
| strach a chamtivost | short | 192 | 41% | 16% | 48% | 17% | 0,0% | +0,04 | -0,23 |
| Keltner průraz | long | 252 | 80% | 69% | 96% | 88% | 48,8% | +0,19 | +0,13 |
| Keltner průraz | short | 252 | 40% | 62% | 54% | 73% | 14,3% | -0,05 | +0,06 |
| protnutí 2 průměrů | long | 16128 | 66% | 53% | 70% | 65% | 8,4% | +0,16 | +0,02 |
| protnutí 2 průměrů | short | 16128 | 31% | 65% | 69% | 52% | 5,0% | -0,07 | +0,08 |
| MACD | long | 504 | 63% | 52% | 76% | 56% | 9,7% | +0,10 | +0,01 |
| MACD | short | 504 | 45% | 56% | 79% | 49% | 7,9% | -0,01 | +0,01 |
| cena × průměr | long | 840 | 54% | 52% | 54% | 48% | 4,5% | +0,02 | +0,00 |
| cena × průměr | short | 840 | 37% | 62% | 88% | 49% | 11,7% | -0,02 | +0,03 |
| momentum ROC | long | 336 | 56% | 50% | 56% | 49% | 3,6% | +0,02 | -0,00 |
| momentum ROC | short | 336 | 32% | 59% | 82% | 41% | 8,6% | -0,04 | +0,02 |
| RSI momentum | long | 252 | 62% | 60% | 73% | 69% | 13,1% | +0,06 | +0,03 |
| RSI momentum | short | 252 | 37% | 64% | 85% | 56% | 11,5% | -0,02 | +0,04 |
| RSI návrat | long | 336 | 23% | 20% | 23% | 24% | 0,0% | -0,09 | -0,10 |
| RSI návrat | short | 336 | 24% | 51% | 35% | 50% | 7,7% | -0,07 | +0,01 |
| Stochastic | long | 168 | 22% | 16% | 17% | 19% | 0,0% | -0,11 | -0,09 |
| Stochastic | short | 168 | 11% | 60% | 29% | 63% | 3,0% | -0,07 | +0,02 |
| Supertrend | long | 252 | 67% | 52% | 81% | 56% | 4,8% | +0,14 | +0,01 |
| Supertrend | short | 252 | 55% | 67% | 77% | 61% | 7,5% | +0,02 | +0,06 |
| sweep & reclaim | long | 168 | 34% | 14% | 21% | 14% | 0,0% | -0,10 | -0,12 |
| sweep & reclaim | short | 168 | 12% | 61% | 23% | 48% | 1,8% | -0,11 | +0,03 |
| průraz s objemem | long | 336 | 80% | 68% | 96% | 82% | 37,8% | +0,36 | +0,17 |
| průraz s objemem | short | 336 | 27% | 62% | 40% | 52% | 6,0% | -0,14 | +0,04 |

## 2. Podle timeframu (všechny rodiny dohromady)

| TF | Směr | OOS > 0 | HOLDOUT > 0 | OOS nad náhodou | HOLDOUT nad náhodou | Medián OOS R | Medián obchodů/měs. |
|---|---|---|---|---|---|---|---|
| 15m | long | 22% | 25% | 81% | 60% | -0,08 | 147 |
| 15m | short | 32% | 2% | 89% | 50% | -0,03 | 203 |
| 1h | long | 61% | 61% | 76% | 53% | +0,05 | 40 |
| 1h | short | 54% | 38% | 72% | 42% | +0,01 | 44 |
| 2h | long | 69% | 62% | 72% | 58% | +0,10 | 20 |
| 2h | short | 41% | 63% | 60% | 38% | -0,02 | 22 |
| 4h | long | 75% | 65% | 70% | 62% | +0,17 | 10 |
| 4h | short | 32% | 75% | 67% | 39% | -0,07 | 11 |
| 6h | long | 77% | 59% | 60% | 66% | +0,44 | 7 |
| 6h | short | 28% | 87% | 70% | 60% | -0,10 | 8 |
| 12h | long | 76% | 57% | 63% | 78% | +0,48 | 4 |
| 12h | short | 22% | 90% | 64% | 64% | -0,18 | 4 |
| 1d | long | 65% | 35% | 57% | 63% | +0,30 | 2 |
| 1d | short | 12% | 89% | 51% | 69% | -0,28 | 2 |

## 3. Kolik dělají poplatky

Podíl všech kombinací s kladným Ø R v OOS a v HOLDOUT podle výše poplatků:

| Poplatky na stranu | OOS > 0 long | OOS > 0 short | HOLDOUT > 0 long | HOLDOUT > 0 short | Projde pravidlem (ze všech) |
|---|---|---|---|---|---|
| 0 % (maker, optimisticky) | 76% | 47% | 65% | 86% | 985 z 33868 |
| 0,05 % (MEXC futures taker) | 64% | 31% | 52% | 63% | 202 z 33868 |
| 0,08 % (MEXC spot taker) | 60% | 23% | 46% | 57% | 144 z 33868 |
| 0,15 % (dřívější testy) | 54% | 14% | 37% | 49% | 64 z 33868 |

## 4. Výběr podle předem stanoveného pravidla (50 nejlepších podle IS t-statistiky na směr)

| Směr | Kombinace | IS n / Ø R | OOS n / Ø R | OOS t | Náhoda OOS p95 | HOLDOUT n / Ø R | Náhoda HOLD p95 | Max. propad R | Obch./měs. | Prošlo |
|---|---|---|---|---|---|---|---|---|---|---|
| long | 2h MACD 19/39/9/signal · d50 · opp | 2019 / +0,31 | 635 / +0,07 | +1,1 | +0,04 | 460 / +0,12 | +0,21 | 64 | 35 | ❌ |
| long | 1h protnutí 2 průměrů sma/30/200/confirm · none · opp | 1178 / +1,67 | 420 / +0,61 | +1,9 | +0,88 | 382 / +0,07 | +0,90 | 245 | 22 | ❌ |
| long | 12h MACD 5/35/5/signal · none · opp | 1591 / +0,32 | 573 / +0,16 | +2,4 | +0,24 | 527 / +0,03 | +0,12 | 73 | 30 | ❌ |
| long | 1h protnutí 2 průměrů sma/40/200/confirm · none · opp | 1071 / +1,82 | 379 / +0,83 | +2,1 | +1,41 | 336 / +0,09 | +0,43 | 246 | 20 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/30/cross · d50 · opp | 2795 / +0,39 | 867 / +0,06 | +0,8 | +0,07 | 618 / +0,10 | +0,38 | 107 | 49 | ❌ |
| long | 6h MACD 12/26/9/signal · none · opp | 1904 / +0,35 | 660 / +0,24 | +2,9 | +0,32 | 653 / +0,01 | +0,12 | 123 | 36 | ❌ |
| long | 6h MACD 19/39/9/signal · none · opp | 1450 / +0,54 | 506 / +0,26 | +2,5 | +0,38 | 495 / +0,06 | +0,17 | 107 | 28 | ❌ |
| long | 4h MACD 5/35/5/signal · d50 · opp | 2312 / +0,18 | 748 / +0,04 | +1,0 | +0,03 | 508 / +0,08 | +0,14 | 43 | 40 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/200/confirm · none · opp | 1773 / +1,05 | 609 / +0,47 | +2,1 | +0,74 | 578 / +0,21 | +0,51 | 253 | 34 | ❌ |
| long | 12h MACD 5/35/5/signal · none · opp_stop | 1591 / +0,41 | 573 / +0,19 | +2,3 | +0,18 | 527 / +0,05 | +0,15 | 93 | 30 | ❌ |
| long | 1h protnutí 2 průměrů sma/30/200/confirm · d50 · opp | 740 / +2,10 | 254 / +0,60 | +1,2 | +0,91 | 178 / +0,87 | +1,64 | 117 | 13 | ❌ |
| long | 1h protnutí 2 průměrů ema/50/60/confirm · none · opp | 1682 / +1,28 | 596 / +0,59 | +2,4 | +0,74 | 586 / +0,08 | +0,44 | 288 | 32 | ❌ |
| long | 1h protnutí 2 průměrů ema/50/200/confirm · none · opp | 1029 / +1,86 | 357 / +0,69 | +2,0 | +1,22 | 336 / +0,00 | +0,59 | 295 | 20 | ❌ |
| long | 2h protnutí 2 průměrů sma/20/200/confirm · none · opp | 633 / +2,38 | 229 / +1,69 | +2,2 | +2,60 | 208 / -0,23 | -0,43 | 192 | 12 | ❌ |
| long | 1h protnutí 2 průměrů sma/20/200/confirm · none · opp | 1381 / +1,36 | 479 / +0,52 | +1,8 | +1,00 | 445 / +0,04 | +0,28 | 289 | 26 | ❌ |
| long | 1h protnutí 2 průměrů ema/40/100/confirm · none · opp | 1515 / +1,24 | 528 / +0,54 | +2,0 | +0,98 | 512 / +0,13 | +0,47 | 291 | 29 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/200/confirm · none · opp | 1075 / +1,58 | 361 / +1,05 | +2,5 | +1,41 | 360 / +0,10 | -0,09 | 180 | 20 | ❌ |
| long | 1h protnutí 2 průměrů ema/40/200/confirm · none · opp | 1125 / +1,64 | 400 / +0,65 | +2,1 | +1,13 | 368 / +0,08 | +0,96 | 283 | 21 | ❌ |
| long | 1h protnutí 2 průměrů sma/40/200/confirm · d50 · opp | 681 / +2,26 | 228 / +0,75 | +1,3 | +1,01 | 157 / +1,40 | +1,68 | 105 | 12 | ❌ |
| long | 4h protnutí 2 průměrů sma/10/100/confirm · none · opp | 558 / +1,95 | 209 / +1,51 | +2,2 | +2,60 | 193 / -0,05 | -0,19 | 123 | 11 | ❌ |
| long | 4h protnutí 2 průměrů sma/10/100/cross · none · opp | 596 / +1,83 | 216 / +1,48 | +2,2 | +2,44 | 201 / -0,04 | -0,17 | 121 | 11 | ❌ |
| long | 1h protnutí 2 průměrů ema/30/100/confirm · none · opp | 1709 / +1,08 | 594 / +0,48 | +2,1 | +0,76 | 586 / +0,14 | +0,31 | 270 | 33 | ❌ |
| long | 2h protnutí 2 průměrů ema/10/30/confirm · none · opp | 2543 / +0,51 | 916 / +0,30 | +2,5 | +0,37 | 879 / +0,08 | +0,10 | 191 | 49 | ❌ |
| long | 4h protnutí 2 průměrů sma/5/30/cross · none · opp | 1771 / +0,57 | 639 / +0,26 | +2,4 | +0,42 | 605 / +0,06 | +0,09 | 137 | 34 | ❌ |
| long | 2h protnutí 2 průměrů ema/40/150/confirm · none · opp | 589 / +2,55 | 225 / +1,68 | +2,0 | +2,46 | 198 / +0,08 | -0,06 | 142 | 11 | ❌ |
| long | 2h protnutí 2 průměrů ema/10/30/cross · none · opp | 2538 / +0,51 | 916 / +0,30 | +2,5 | +0,35 | 879 / +0,08 | +0,10 | 191 | 49 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/60/cross · none · opp | 2311 / +0,65 | 813 / +0,33 | +2,5 | +0,51 | 777 / +0,05 | -0,01 | 210 | 44 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/150/confirm · none · opp | 2011 / +1,01 | 696 / +0,43 | +2,2 | +0,69 | 687 / +0,09 | +0,03 | 302 | 38 | ❌ |
| long | 2h protnutí 2 průměrů sma/10/200/confirm · none · opp | 851 / +1,89 | 292 / +1,27 | +2,4 | +2,09 | 282 / -0,02 | -0,19 | 194 | 16 | ❌ |
| long | 1h protnutí 2 průměrů sma/20/150/confirm · none · opp | 1581 / +1,23 | 530 / +0,61 | +2,2 | +0,92 | 529 / +0,12 | +0,24 | 288 | 30 | ❌ |
| long | 4h MACD 19/39/9/signal · none · opp | 2222 / +0,35 | 767 / +0,24 | +3,1 | +0,24 | 747 / +0,04 | +0,18 | 152 | 42 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/30/confirm · d50 · opp | 2938 / +0,36 | 963 / +0,08 | +1,1 | +0,05 | 684 / +0,16 | +0,26 | 124 | 52 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/200/pullback · none · opp | 832 / +1,73 | 277 / +1,34 | +2,1 | +1,58 | 256 / +0,17 | +0,25 | 139 | 15 | ❌ |
| long | 2h MACD 12/26/9/zero · none · opp | 2512 / +0,50 | 916 / +0,28 | +2,4 | +0,35 | 860 / +0,08 | +0,05 | 187 | 49 | ❌ |
| long | 4h protnutí 2 průměrů sma/10/60/confirm · none · opp | 837 / +1,26 | 298 / +0,77 | +2,0 | +1,18 | 294 / +0,03 | +0,35 | 110 | 16 | ❌ |
| long | 1h protnutí 2 průměrů ema/40/150/confirm · none · opp | 1297 / +1,37 | 464 / +0,55 | +1,8 | +1,26 | 417 / +0,02 | +0,53 | 279 | 25 | ❌ |
| long | 4h protnutí 2 průměrů sma/5/30/confirm · none · opp | 1686 / +0,59 | 600 / +0,28 | +2,5 | +0,47 | 572 / +0,06 | +0,11 | 134 | 32 | ❌ |
| long | 1h protnutí 2 průměrů sma/50/200/confirm · none · opp | 1028 / +1,82 | 346 / +0,71 | +1,8 | +1,13 | 319 / +0,20 | +0,80 | 236 | 19 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/60/confirm · none · opp | 2201 / +0,67 | 775 / +0,33 | +2,4 | +0,53 | 733 / +0,06 | +0,12 | 202 | 42 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/50/cross · none · opp | 2572 / +0,56 | 905 / +0,26 | +2,5 | +0,32 | 854 / +0,06 | +0,10 | 213 | 49 | ❌ |
| long | 2h protnutí 2 průměrů sma/10/60/cross · none · opp | 1777 / +0,82 | 631 / +0,40 | +2,3 | +0,71 | 610 / +0,03 | +0,18 | 210 | 34 | ❌ |
| long | 2h protnutí 2 průměrů sma/10/60/confirm · none · opp | 1699 / +0,85 | 592 / +0,44 | +2,4 | +0,73 | 575 / +0,05 | +0,04 | 201 | 32 | ❌ |
| long | 4h protnutí 2 průměrů ema/20/30/cross · none · opp | 925 / +1,15 | 338 / +0,69 | +2,0 | +1,08 | 318 / -0,01 | +0,06 | 139 | 18 | ❌ |
| long | 12h MACD 19/39/9/signal · none · opp | 698 / +0,78 | 240 / +0,65 | +2,9 | +0,83 | 212 / +0,12 | +0,13 | 49 | 13 | ❌ |
| long | 1h protnutí 2 průměrů ema/50/60/cross · none · opp | 1621 / +1,27 | 582 / +0,56 | +2,2 | +0,92 | 579 / +0,09 | +0,28 | 288 | 32 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/50/confirm · none · opp | 2445 / +0,59 | 859 / +0,27 | +2,5 | +0,40 | 816 / +0,06 | +0,08 | 210 | 47 | ❌ |
| long | 4h momentum ROC 20 · none · opp | 3915 / +0,23 | 1370 / +0,08 | +1,7 | +0,18 | 1205 / +0,02 | +0,09 | 171 | 74 | ❌ |
| long | 4h protnutí 2 průměrů ema/10/60/confirm · none · opp | 846 / +1,33 | 313 / +0,70 | +2,0 | +1,49 | 293 / +0,09 | +0,19 | 126 | 16 | ❌ |
| long | 4h protnutí 2 průměrů ema/20/30/confirm · none · opp | 929 / +1,14 | 338 / +0,69 | +2,0 | +1,18 | 318 / -0,01 | +0,08 | 139 | 18 | ❌ |
| long | 4h protnutí 2 průměrů ema/10/60/cross · none · opp | 844 / +1,34 | 313 / +0,70 | +2,0 | +1,24 | 293 / +0,09 | +0,17 | 126 | 16 | ❌ |
| short | 4h průraz s objemem 20/2.5 · none · target | 549 / +0,24 | 261 / +0,19 | +2,6 | +0,12 | 223 / +0,03 | +0,14 | 50 | 12 | ❌ |
| short | 6h MACD 19/39/9/signal · d50 · opp_stop | 585 / +0,30 | 224 / +0,12 | +1,2 | +0,05 | 296 / +0,11 | +0,16 | 45 | 13 | ❌ |
| short | 4h průraz s objemem 55/2.5 · d50 · target | 270 / +0,28 | 137 / +0,00 | +0,0 | +0,12 | 138 / +0,05 | +0,18 | 22 | 6 | ❌ |
| short | 6h MACD 12/26/9/signal · d50 · opp_stop | 755 / +0,23 | 310 / +0,03 | +0,3 | +0,04 | 384 / -0,02 | +0,12 | 70 | 16 | ❌ |
| short | 4h průraz s objemem 20/1.5 · d200 · target | 526 / +0,19 | 188 / -0,01 | -0,1 | +0,00 | 278 / -0,04 | +0,10 | 44 | 11 | ❌ |
| short | 4h průraz s objemem 55/2.5 · none · target | 363 / +0,23 | 179 / +0,08 | +0,9 | +0,07 | 171 / +0,04 | +0,19 | 35 | 8 | ❌ |
| short | 4h průraz s objemem 20/2.5 · d200 · target | 283 / +0,26 | 115 / +0,07 | +0,6 | +0,11 | 160 / -0,07 | +0,23 | 38 | 6 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/60/pullback · d50 · trail | 1481 / +0,18 | 597 / -0,11 | -1,7 | +0,13 | 589 / -0,00 | +0,06 | 121 | 30 | ❌ |
| short | 4h průraz s objemem 20/2.5 · d50 · target | 324 / +0,23 | 169 / +0,02 | +0,2 | +0,09 | 158 / -0,03 | +0,12 | 33 | 7 | ❌ |
| short | 4h průraz s objemem 55/2.5 · d200 · target | 219 / +0,28 | 91 / +0,02 | +0,1 | +0,08 | 134 / +0,01 | +0,20 | 24 | 5 | ❌ |
| short | 2h Bollinger průraz 50/2.5 · d50 · target | 725 / +0,15 | 291 / +0,11 | +1,5 | +0,06 | 301 / +0,02 | +0,08 | 39 | 15 | ❌ |
| short | 4h MACD 19/39/9/signal · d50 · opp_stop | 916 / +0,20 | 362 / +0,07 | +0,9 | +0,05 | 440 / -0,09 | +0,13 | 82 | 19 | ❌ |
| short | 6h MACD 19/39/9/signal · d50 · opp | 585 / +0,20 | 224 / +0,07 | +0,8 | +0,08 | 296 / +0,01 | +0,09 | 45 | 13 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/100/confirm · d50 · trail | 2117 / +0,13 | 869 / -0,02 | -0,3 | +0,08 | 881 / -0,01 | +0,06 | 109 | 44 | ❌ |
| short | 6h MACD 19/39/9/signal · d200 · opp_stop | 620 / +0,24 | 178 / +0,04 | +0,4 | -0,01 | 351 / +0,08 | +0,17 | 57 | 13 | ❌ |
| short | 1h protnutí 2 průměrů sma/40/50/pullback · d50 · trail | 1678 / +0,15 | 626 / -0,07 | -1,0 | +0,11 | 637 / +0,07 | +0,06 | 112 | 33 | ❌ |
| short | 6h protnutí 2 průměrů ema/50/100/cross · none · target | 178 / +0,27 | 74 / -0,16 | -1,2 | +0,26 | 57 / +0,28 | +0,22 | 26 | 3 | ❌ |
| short | 1h Bollinger průraz 50/2.0 · d50 · trail | 1557 / +0,16 | 656 / +0,07 | +0,9 | +0,09 | 693 / +0,03 | +0,03 | 93 | 33 | ❌ |
| short | 2h protnutí 2 průměrů ema/30/200/cross · none · target | 482 / +0,17 | 202 / +0,21 | +2,5 | +0,09 | 175 / +0,04 | +0,16 | 30 | 10 | ❌ |
| short | 1h protnutí 2 průměrů ema/20/100/cross · d50 · opp_stop | 785 / +0,46 | 327 / +0,15 | +0,9 | +0,15 | 389 / +0,05 | +0,18 | 116 | 17 | ❌ |
| short | 12h protnutí 2 průměrů ema/5/150/cross · none · trail | 162 / +0,37 | 86 / -0,24 | -2,2 | +0,06 | 53 / +0,99 | +0,51 | 33 | 3 | ❌ |
| short | 4h Bollinger průraz 50/2.5 · d200 · target | 302 / +0,21 | 98 / +0,16 | +1,3 | +0,07 | 145 / +0,18 | +0,22 | 23 | 6 | ❌ |
| short | 1h protnutí 2 průměrů sma/30/50/pullback · d50 · trail | 1797 / +0,14 | 706 / +0,04 | +0,6 | +0,08 | 746 / +0,06 | +0,08 | 77 | 37 | ❌ |
| short | 1h Bollinger průraz 50/2.0 · d200 · trail | 1419 / +0,15 | 469 / +0,07 | +0,9 | +0,08 | 749 / -0,00 | +0,05 | 93 | 30 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/60/confirm · d50 · trail | 2279 / +0,12 | 902 / -0,01 | -0,2 | +0,07 | 907 / +0,07 | +0,10 | 84 | 46 | ❌ |
| short | 2h protnutí 2 průměrů sma/20/30/pullback · d50 · trail | 1045 / +0,17 | 373 / -0,02 | -0,2 | +0,07 | 402 / +0,07 | +0,18 | 58 | 21 | ❌ |
| short | 1h protnutí 2 průměrů ema/50/60/confirm · d50 · trail | 2341 / +0,12 | 963 / +0,02 | +0,3 | +0,08 | 1061 / +0,02 | +0,10 | 108 | 49 | ❌ |
| short | 6h MACD 12/26/9/signal · d200 · opp_stop | 790 / +0,17 | 244 / +0,04 | +0,5 | -0,01 | 450 / +0,01 | +0,09 | 69 | 17 | ❌ |
| short | 1h cena × průměr ema/50 · d50 · trail | 2984 / +0,10 | 1190 / +0,04 | +0,7 | +0,07 | 1349 / +0,06 | +0,09 | 114 | 63 | ❌ |
| short | 2h protnutí 2 průměrů ema/40/150/cross · none · target | 496 / +0,15 | 203 / +0,09 | +1,1 | +0,17 | 188 / -0,03 | +0,09 | 38 | 10 | ❌ |
| short | 6h protnutí 2 průměrů ema/20/200/cross · none · target | 178 / +0,25 | 91 / -0,06 | -0,5 | +0,14 | 64 / +0,04 | +0,25 | 25 | 4 | ❌ |
| short | 2h protnutí 2 průměrů sma/5/60/pullback · d50 · trail | 1551 / +0,13 | 637 / -0,01 | -0,1 | +0,11 | 703 / -0,05 | +0,17 | 124 | 33 | ❌ |
| short | 2h protnutí 2 průměrů sma/40/50/cross · d50 · opp_stop | 995 / +0,24 | 407 / -0,01 | -0,1 | +0,03 | 434 / +0,09 | +0,09 | 87 | 21 | ❌ |
| short | 6h MACD 12/26/9/signal · d50 · opp | 755 / +0,14 | 310 / +0,00 | +0,0 | +0,00 | 384 / -0,04 | +0,07 | 67 | 16 | ❌ |
| short | 2h protnutí 2 průměrů sma/10/60/pullback · d50 · opp | 786 / +0,25 | 312 / -0,10 | -1,0 | -0,02 | 336 / +0,03 | +0,29 | 100 | 16 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/100/pullback · d50 · trail | 1638 / +0,14 | 673 / -0,10 | -1,6 | +0,15 | 650 / -0,04 | +0,07 | 148 | 34 | ❌ |
| short | 6h Supertrend 20/3.0 · d200 · opp | 198 / +0,42 | 70 / +0,21 | +1,3 | -0,34 | 116 / +0,16 | +0,50 | 48 | 4 | ❌ |
| short | 1h protnutí 2 průměrů ema/50/60/confirm · d50 · opp | 915 / +0,35 | 385 / -0,13 | -0,9 | +0,05 | 422 / +0,02 | +0,31 | 169 | 20 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/150/cross · d50 · opp_stop | 551 / +0,52 | 233 / +0,14 | +0,7 | +0,01 | 261 / -0,25 | +0,62 | 116 | 12 | ❌ |
| short | 12h MACD 5/35/5/signal · d200 · opp_stop | 652 / +0,13 | 198 / +0,05 | +0,7 | +0,04 | 373 / +0,05 | +0,05 | 39 | 14 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/60/pullback · d50 · trail | 2032 / +0,12 | 849 / -0,02 | -0,3 | +0,05 | 861 / -0,01 | +0,09 | 106 | 42 | ❌ |
| short | 6h protnutí 2 průměrů ema/30/150/cross · none · target | 178 / +0,24 | 84 / +0,03 | +0,2 | +0,27 | 58 / +0,25 | +0,23 | 20 | 4 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/100/pullback · none · trail | 2776 / +0,10 | 1029 / -0,04 | -0,7 | +0,08 | 924 / +0,02 | +0,07 | 152 | 54 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/50/confirm · d50 · opp_stop | 1745 / +0,23 | 722 / -0,02 | -0,2 | -0,01 | 762 / +0,12 | +0,18 | 177 | 37 | ❌ |
| short | 1h protnutí 2 průměrů sma/30/100/pullback · d50 · trail | 2023 / +0,12 | 816 / -0,03 | -0,4 | +0,16 | 873 / -0,08 | +0,07 | 172 | 42 | ❌ |
| short | 6h protnutí 2 průměrů ema/30/100/cross · d50 · target | 155 / +0,26 | 65 / +0,11 | +0,8 | +0,01 | 60 / -0,14 | +0,26 | 21 | 3 | ❌ |
| short | 4h průraz s objemem 20/1.5 · none · target | 1021 / +0,10 | 423 / +0,09 | +1,6 | +0,01 | 375 / -0,01 | +0,12 | 62 | 21 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/200/cross · d50 · opp_stop | 459 / +0,61 | 211 / +0,25 | +1,1 | -0,07 | 249 / -0,44 | +0,47 | 128 | 10 | ❌ |
| short | 2h protnutí 2 průměrů sma/40/50/confirm · d50 · trail | 1240 / +0,14 | 500 / +0,03 | +0,4 | +0,13 | 578 / -0,03 | +0,21 | 90 | 26 | ❌ |
| short | 4h Donchian průraz 20 · d200 · target | 697 / +0,12 | 256 / +0,10 | +1,2 | +0,03 | 338 / +0,04 | +0,15 | 50 | 15 | ❌ |

## 5. Všechny kombinace, které splní kritéria (bez pořadí v IS) – kandidáti, ne důkaz

Splní je **202** z 33868 způsobilých kombinací. Čistou náhodou by to bylo řádově 25 (OOS i HOLDOUT nad p95 ≈ 0,25 %, k tomu t ≥ 2 a kladné IS). Kombinace v rámci rodiny jsou si podobné, takže skutečně nezávislých nálezů je méně.

| Směr | Kombinace | IS Ø R | OOS n / Ø R / t | HOLDOUT n / Ø R | Max. propad R | Obch./měs. | Ø % na obchod (OOS) |
|---|---|---|---|---|---|---|---|
| short | 6h Supertrend 10/3.0 · none · target | +0,03 | 201 / +0,36 / +4,1 | 171 / +0,24 | 50 | 10 | +1,85 |
| short | 6h Supertrend 10/3.0 · d200 · target | +0,14 | 71 / +0,58 / +4,1 | 110 / +0,23 | 19 | 4 | +3,68 |
| short | 6h Supertrend 10/3.0 · d50 · target | +0,09 | 80 / +0,52 / +3,9 | 91 / +0,24 | 24 | 4 | +3,45 |
| short | 2h Keltner průraz 2.5 · none · target | +0,04 | 430 / +0,20 / +3,5 | 399 / +0,10 | 54 | 22 | +0,44 |
| long | 1h Bollinger průraz 50/2.5 · none · opp_stop | +0,40 | 733 / +0,57 / +3,2 | 704 / +0,34 | 135 | 43 | +0,78 |
| long | 1h Bollinger průraz 50/2.5 · none · opp | +0,43 | 645 / +0,49 / +3,1 | 613 / +0,24 | 141 | 37 | +0,91 |
| short | 6h protnutí 2 průměrů ema/50/100/pullback · none · target | +0,01 | 177 / +0,28 / +3,1 | 167 / +0,20 | 41 | 8 | +1,83 |
| long | 1h protnutí 2 průměrů ema/20/30/confirm · none · opp | +0,39 | 1281 / +0,31 / +3,0 | 1253 / +0,03 | 277 | 72 | +0,56 |
| long | 2h RSI momentum 55 · none · opp_stop | +0,24 | 1524 / +0,19 / +3,0 | 1458 / +0,05 | 226 | 86 | +0,37 |
| long | 2h RSI momentum 60 · none · opp_stop | +0,37 | 984 / +0,28 / +3,0 | 932 / +0,14 | 169 | 55 | +0,56 |
| short | 2h protnutí 2 průměrů sma/20/50/cross · none · target | +0,03 | 561 / +0,15 / +2,9 | 537 / +0,10 | 49 | 31 | +0,36 |
| long | 2h protnutí 2 průměrů ema/5/50/cross · none · trail | +0,18 | 797 / +0,22 / +2,9 | 784 / +0,09 | 111 | 43 | +0,50 |
| short | 1h protnutí 2 průměrů sma/50/100/cross · none · trail | +0,02 | 575 / +0,23 / +2,9 | 533 / +0,12 | 103 | 31 | +0,37 |
| long | 1h Bollinger průraz 50/2.0 · none · opp_stop | +0,36 | 1067 / +0,38 / +2,9 | 1023 / +0,16 | 201 | 61 | +0,48 |
| short | 2h protnutí 2 průměrů ema/40/200/cross · none · target | +0,08 | 175 / +0,26 / +2,8 | 155 / +0,14 | 18 | 9 | +0,93 |
| long | 6h Bollinger průraz 50/2.5 · d50 · target | +0,19 | 122 / +0,31 / +2,8 | 88 / +0,07 | 34 | 7 | +1,84 |
| long | 6h MACD 5/35/5/signal · none · opp_stop | +0,16 | 1140 / +0,13 / +2,7 | 1071 / +0,04 | 120 | 64 | +0,45 |
| long | 1h průraz s objemem 55/1.5 · none · opp | +0,78 | 553 / +0,57 / +2,7 | 478 / +0,45 | 195 | 29 | +0,95 |
| long | 1h průraz s objemem 55/2.5 · none · opp | +1,06 | 434 / +0,65 / +2,7 | 385 / +0,52 | 125 | 22 | +1,18 |
| long | 2h MACD 19/39/9/signal · none · opp | +0,15 | 1528 / +0,12 / +2,7 | 1433 / +0,04 | 174 | 84 | +0,42 |
| long | 1h protnutí 2 průměrů sma/10/50/confirm · none · opp | +0,30 | 1347 / +0,26 / +2,7 | 1252 / +0,04 | 310 | 75 | +0,51 |
| short | 12h protnutí 2 průměrů ema/20/50/cross · none · target | +0,12 | 78 / +0,36 / +2,7 | 69 / +0,16 | 16 | 4 | +3,09 |
| short | 6h protnutí 2 průměrů ema/50/150/pullback · none · target | +0,01 | 174 / +0,24 / +2,6 | 178 / +0,17 | 41 | 9 | +1,56 |
| long | 1h protnutí 2 průměrů ema/10/100/cross · none · opp_stop | +0,57 | 957 / +0,37 / +2,6 | 951 / +0,20 | 249 | 52 | +0,48 |
| long | 12h MACD 12/26/9/signal · none · opp_stop | +0,68 | 315 / +0,52 / +2,6 | 292 / +0,12 | 68 | 17 | +2,37 |
| long | 2h Bollinger průraz 50/2.0 · none · opp | +0,77 | 448 / +0,46 / +2,6 | 401 / +0,31 | 120 | 24 | +1,21 |
| short | 6h protnutí 2 průměrů ema/10/50/cross · none · target | +0,06 | 207 / +0,22 / +2,6 | 190 / +0,16 | 37 | 10 | +1,58 |
| long | 2h protnutí 2 průměrů sma/5/150/cross · none · trail | +0,20 | 434 / +0,28 / +2,6 | 410 / +0,26 | 60 | 23 | +0,69 |
| long | 12h MACD 19/39/9/signal · none · opp_stop | +0,89 | 240 / +0,76 / +2,6 | 212 / +0,18 | 44 | 13 | +3,72 |
| long | 6h protnutí 2 průměrů ema/50/60/cross · none · target | +0,06 | 88 / +0,34 / +2,6 | 84 / +0,40 | 29 | 5 | +1,80 |
| long | 1h Donchian průraz 55 · none · opp | +0,75 | 607 / +0,51 / +2,6 | 538 / +0,33 | 205 | 33 | +0,81 |
| short | 2h protnutí 2 průměrů sma/10/30/cross · none · trail | +0,00 | 901 / +0,14 / +2,6 | 859 / +0,08 | 181 | 50 | +0,14 |
| long | 6h Bollinger průraz 50/2.5 · none · target | +0,20 | 170 / +0,25 / +2,6 | 135 / +0,07 | 35 | 10 | +1,41 |
| long | 1h Bollinger průraz 50/2.5 · none · trail | +0,20 | 738 / +0,22 / +2,5 | 698 / +0,14 | 94 | 43 | +0,44 |
| long | 4h cena × průměr sma/20 · none · opp_stop | +0,21 | 1518 / +0,13 / +2,5 | 1407 / +0,05 | 177 | 84 | +0,36 |
| long | 6h Bollinger průraz 20/2.0 · none · opp | +0,61 | 322 / +0,42 / +2,5 | 269 / +0,28 | 60 | 17 | +1,69 |
| short | 6h protnutí 2 průměrů ema/40/100/pullback · none · target | +0,04 | 192 / +0,22 / +2,5 | 200 / +0,12 | 38 | 10 | +1,38 |
| short | 1h protnutí 2 průměrů sma/20/30/pullback · d200 · trail | +0,01 | 537 / +0,20 / +2,5 | 857 / +0,05 | 82 | 36 | +0,25 |
| short | 1h protnutí 2 průměrů sma/40/50/cross · none · trail | +0,02 | 1251 / +0,13 / +2,5 | 1174 / +0,06 | 119 | 70 | +0,09 |
| long | 6h RSI momentum 60 · none · opp_stop | +0,87 | 325 / +0,64 / +2,5 | 305 / +0,25 | 93 | 18 | +2,13 |

Podle rodiny a timeframu: protnutí 2 průměrů 2h long: 17; protnutí 2 průměrů 4h long: 15; protnutí 2 průměrů 6h long: 13; Bollinger průraz 2h long: 12; Bollinger průraz 6h long: 11; Bollinger průraz 4h long: 9; protnutí 2 průměrů 12h long: 9; protnutí 2 průměrů 1h long: 9; protnutí 2 průměrů 6h short: 7; protnutí 2 průměrů 1h short: 7; Keltner průraz 6h long: 7; Bollinger průraz 1h long: 7; Bollinger průraz 12h long: 7; průraz s objemem 1h long: 6; Donchian průraz 1h long: 5.

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