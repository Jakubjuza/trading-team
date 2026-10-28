# Atlas strategií – 15 rodin, 7 timeframů, poplatky MEXC (27. 10. 2026)

Otázka: je mezi běžnými pravidlovými strategiemi na kterémkoli timeframu něco, co po poplatcích MEXC vydělává spolehlivěji než náhoda? Metoda stanovená předem je v hlavičce `research/experiments/strategy_atlas.py`.

- **41 664 kombinací** (15 rodin, 248 variant × 7 timeframů × 3 filtry × 4 výstupy × long/short), 8 mincí.
- 12h: 5952 kombinací, 1259 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 15m: 5952 kombinací, 4464 s, data od BTC 01/2022, ETH 01/2022, SOL 01/2022, XRP 01/2022, ADA 01/2022, LINK 01/2022, AVAX 01/2022, DOGE 01/2022
- 1d: 5952 kombinací, 1225 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 1h: 5952 kombinací, 1347 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 2h: 5952 kombinací, 901 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 4h: 5952 kombinací, 749 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- 6h: 5952 kombinací, 844 s, data od BTC 01/2019, ETH 01/2019, SOL 09/2020, XRP 01/2019, ADA 01/2019, LINK 01/2019, AVAX 09/2020, DOGE 07/2019
- Poplatky na stranu: **MEXC futures taker 0,02 % + skluz 0,03 % = 0,05 % (rozhoduje)**; MEXC spot taker 0,08 %; maker 0 % (optimistická mez); 0,15 % (dřívější testy). Funding nezapočten. Poplatky MEXC podle [MEXC, 11/2025](https://www.mexc.com/ru-RU/crypto-pulse/article/mexc-trading-fees-complete-guide-39643).
- IS do 12/2023 (15M od 1/2022), OOS 1/2024–6/2025, HOLDOUT 7/2025–dnes. R = výsledek po poplatcích / riziko (vzdálenost stopu; bez stopu 2 ATR).

## 1. Mají rodiny strategií výhodu? (hlavní scénář poplatků)

„Nad náhodou“ = podíl kombinací, jejichž Ø R v daném období je nad mediánem jejich vlastních náhodných vstupů (bez výhody by to bylo ~50 %). „Obě nad p95“ = OOS i HOLDOUT nad 95. percentilem náhody (čistou náhodou ~0,25 %).

| Rodina | Směr | Kombinací | OOS > 0 | HOLDOUT > 0 | OOS nad náhodou | HOLDOUT nad náhodou | Obě nad p95 | Medián OOS R | Medián HOLDOUT R |
|---|---|---|---|---|---|---|---|---|---|
| Bollinger průraz | long | 336 | 81% | 76% | 93% | 90% | 50,6% | +0,25 | +0,18 |
| Bollinger průraz | short | 336 | 32% | 72% | 53% | 85% | 12,8% | -0,06 | +0,08 |
| Bollinger návrat | long | 336 | 21% | 30% | 17% | 31% | 0,0% | -0,11 | -0,07 |
| Bollinger návrat | short | 336 | 33% | 49% | 44% | 43% | 4,2% | -0,05 | +0,00 |
| svíčkové vzory | long | 168 | 50% | 44% | 60% | 46% | 0,6% | -0,00 | -0,01 |
| svíčkové vzory | short | 168 | 23% | 58% | 62% | 54% | 2,4% | -0,06 | +0,03 |
| Donchian průraz | long | 420 | 80% | 64% | 95% | 82% | 30,7% | +0,25 | +0,09 |
| Donchian průraz | short | 420 | 30% | 66% | 48% | 50% | 2,4% | -0,08 | +0,04 |
| Keltner průraz | long | 252 | 80% | 69% | 96% | 88% | 49,6% | +0,19 | +0,14 |
| Keltner průraz | short | 252 | 40% | 65% | 54% | 77% | 17,9% | -0,05 | +0,06 |
| protnutí 2 průměrů | long | 16128 | 66% | 55% | 70% | 64% | 8,1% | +0,16 | +0,03 |
| protnutí 2 průměrů | short | 16128 | 31% | 65% | 69% | 54% | 5,4% | -0,07 | +0,07 |
| MACD | long | 504 | 63% | 56% | 75% | 55% | 8,5% | +0,10 | +0,03 |
| MACD | short | 504 | 45% | 58% | 79% | 51% | 9,3% | -0,01 | +0,02 |
| cena × průměr | long | 840 | 54% | 56% | 55% | 48% | 4,6% | +0,02 | +0,02 |
| cena × průměr | short | 840 | 37% | 60% | 89% | 51% | 12,3% | -0,02 | +0,02 |
| momentum ROC | long | 336 | 56% | 52% | 54% | 53% | 4,5% | +0,02 | +0,01 |
| momentum ROC | short | 336 | 32% | 56% | 81% | 42% | 8,9% | -0,04 | +0,01 |
| RSI momentum | long | 252 | 62% | 63% | 75% | 67% | 13,5% | +0,06 | +0,05 |
| RSI momentum | short | 252 | 37% | 68% | 85% | 61% | 11,9% | -0,02 | +0,04 |
| RSI návrat | long | 336 | 23% | 20% | 25% | 22% | 0,0% | -0,09 | -0,10 |
| RSI návrat | short | 336 | 24% | 46% | 37% | 45% | 6,8% | -0,07 | -0,01 |
| Stochastic | long | 168 | 22% | 24% | 18% | 23% | 0,0% | -0,11 | -0,07 |
| Stochastic | short | 168 | 11% | 57% | 27% | 60% | 2,4% | -0,07 | +0,02 |
| Supertrend | long | 252 | 67% | 58% | 81% | 58% | 3,6% | +0,14 | +0,03 |
| Supertrend | short | 252 | 55% | 68% | 79% | 60% | 5,6% | +0,02 | +0,06 |
| sweep & reclaim | long | 168 | 34% | 14% | 20% | 12% | 0,0% | -0,10 | -0,11 |
| sweep & reclaim | short | 168 | 12% | 57% | 23% | 47% | 1,2% | -0,11 | +0,03 |
| průraz s objemem | long | 336 | 80% | 69% | 96% | 82% | 38,4% | +0,36 | +0,19 |
| průraz s objemem | short | 336 | 27% | 62% | 41% | 57% | 6,2% | -0,14 | +0,06 |

## 2. Podle timeframu (všechny rodiny dohromady)

| TF | Směr | OOS > 0 | HOLDOUT > 0 | OOS nad náhodou | HOLDOUT nad náhodou | Medián OOS R | Medián obchodů/měs. |
|---|---|---|---|---|---|---|---|
| 15m | long | 22% | 27% | 81% | 61% | -0,08 | 147 |
| 15m | short | 32% | 2% | 88% | 53% | -0,03 | 202 |
| 1h | long | 61% | 65% | 77% | 54% | +0,05 | 40 |
| 1h | short | 54% | 43% | 71% | 45% | +0,01 | 44 |
| 2h | long | 69% | 65% | 71% | 59% | +0,10 | 20 |
| 2h | short | 41% | 66% | 61% | 41% | -0,02 | 22 |
| 4h | long | 76% | 67% | 71% | 60% | +0,18 | 10 |
| 4h | short | 32% | 78% | 67% | 41% | -0,07 | 11 |
| 6h | long | 77% | 61% | 61% | 63% | +0,44 | 7 |
| 6h | short | 28% | 84% | 71% | 60% | -0,10 | 8 |
| 12h | long | 76% | 59% | 62% | 76% | +0,48 | 4 |
| 12h | short | 22% | 87% | 65% | 65% | -0,18 | 4 |
| 1d | long | 66% | 39% | 59% | 64% | +0,32 | 2 |
| 1d | short | 11% | 89% | 51% | 75% | -0,28 | 2 |

## 3. Kolik dělají poplatky

Podíl všech kombinací s kladným Ø R v OOS a v HOLDOUT podle výše poplatků:

| Poplatky na stranu | OOS > 0 long | OOS > 0 short | HOLDOUT > 0 long | HOLDOUT > 0 short | Projde pravidlem (ze všech) |
|---|---|---|---|---|---|
| 0 % (maker, optimisticky) | 76% | 47% | 66% | 87% | 1019 z 33840 |
| 0,05 % (MEXC futures taker) | 64% | 31% | 55% | 64% | 209 z 33840 |
| 0,08 % (MEXC spot taker) | 61% | 23% | 49% | 57% | 144 z 33840 |
| 0,15 % (dřívější testy) | 54% | 14% | 40% | 49% | 65 z 33840 |

## 4. Výběr podle předem stanoveného pravidla (50 nejlepších podle IS t-statistiky na směr)

| Směr | Kombinace | IS n / Ø R | OOS n / Ø R | OOS t | Náhoda OOS p95 | HOLDOUT n / Ø R | Náhoda HOLD p95 | Max. propad R | Obch./měs. | Prošlo |
|---|---|---|---|---|---|---|---|---|---|---|
| long | 2h MACD 19/39/9/signal · d50 · opp | 2019 / +0,31 | 635 / +0,07 | +1,1 | +0,03 | 459 / +0,13 | +0,16 | 64 | 35 | ❌ |
| long | 1h protnutí 2 průměrů sma/30/200/confirm · none · opp | 1178 / +1,67 | 420 / +0,61 | +1,9 | +0,80 | 372 / +0,16 | +0,60 | 245 | 22 | ❌ |
| long | 12h MACD 5/35/5/signal · none · opp | 1591 / +0,32 | 573 / +0,16 | +2,4 | +0,24 | 511 / +0,06 | +0,14 | 73 | 30 | ❌ |
| long | 1h protnutí 2 průměrů sma/40/200/confirm · none · opp | 1071 / +1,82 | 379 / +0,83 | +2,1 | +1,08 | 329 / +0,17 | +0,51 | 246 | 20 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/30/cross · d50 · opp | 2795 / +0,39 | 867 / +0,06 | +0,8 | +0,10 | 616 / +0,11 | +0,37 | 107 | 49 | ❌ |
| long | 6h MACD 12/26/9/signal · none · opp | 1904 / +0,35 | 660 / +0,24 | +2,9 | +0,33 | 636 / +0,04 | +0,13 | 123 | 36 | ❌ |
| long | 6h MACD 19/39/9/signal · none · opp | 1450 / +0,54 | 506 / +0,26 | +2,5 | +0,38 | 480 / +0,11 | +0,18 | 107 | 28 | ❌ |
| long | 4h MACD 5/35/5/signal · d50 · opp | 2312 / +0,18 | 748 / +0,04 | +1,0 | +0,02 | 507 / +0,08 | +0,16 | 43 | 41 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/200/confirm · none · opp | 1773 / +1,05 | 609 / +0,47 | +2,1 | +0,78 | 564 / +0,27 | +0,32 | 253 | 34 | ❌ |
| long | 12h MACD 5/35/5/signal · none · opp_stop | 1591 / +0,41 | 573 / +0,19 | +2,3 | +0,16 | 511 / +0,08 | +0,10 | 93 | 30 | ❌ |
| long | 1h protnutí 2 průměrů sma/30/200/confirm · d50 · opp | 740 / +2,10 | 254 / +0,60 | +1,2 | +1,10 | 178 / +0,87 | +1,66 | 117 | 13 | ❌ |
| long | 1h protnutí 2 průměrů ema/50/60/confirm · none · opp | 1682 / +1,28 | 596 / +0,59 | +2,4 | +1,05 | 567 / +0,16 | +0,70 | 288 | 32 | ❌ |
| long | 1h protnutí 2 průměrů ema/50/200/confirm · none · opp | 1029 / +1,86 | 357 / +0,69 | +2,0 | +1,13 | 330 / +0,06 | +0,48 | 295 | 20 | ❌ |
| long | 2h protnutí 2 průměrů sma/20/200/confirm · none · opp | 633 / +2,38 | 229 / +1,69 | +2,2 | +2,12 | 205 / -0,19 | -0,00 | 192 | 12 | ❌ |
| long | 1h protnutí 2 průměrů sma/20/200/confirm · none · opp | 1381 / +1,36 | 479 / +0,52 | +1,8 | +0,85 | 435 / +0,11 | +0,56 | 289 | 26 | ❌ |
| long | 1h protnutí 2 průměrů ema/40/100/confirm · none · opp | 1515 / +1,24 | 528 / +0,54 | +2,0 | +1,00 | 496 / +0,22 | +0,31 | 291 | 29 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/200/confirm · none · opp | 1075 / +1,58 | 361 / +1,05 | +2,5 | +1,28 | 355 / +0,14 | +0,15 | 180 | 20 | ❌ |
| long | 1h protnutí 2 průměrů ema/40/200/confirm · none · opp | 1125 / +1,64 | 400 / +0,65 | +2,1 | +0,92 | 360 / +0,15 | +0,76 | 283 | 21 | ❌ |
| long | 1h protnutí 2 průměrů sma/40/200/confirm · d50 · opp | 681 / +2,26 | 228 / +0,75 | +1,3 | +1,30 | 156 / +1,44 | +1,72 | 105 | 12 | ❌ |
| long | 4h protnutí 2 průměrů sma/10/100/confirm · none · opp | 558 / +1,95 | 209 / +1,51 | +2,2 | +2,21 | 191 / -0,04 | -0,24 | 123 | 11 | ❌ |
| long | 4h protnutí 2 průměrů sma/10/100/cross · none · opp | 596 / +1,83 | 216 / +1,48 | +2,2 | +2,53 | 199 / -0,03 | +0,13 | 121 | 11 | ❌ |
| long | 1h protnutí 2 průměrů ema/30/100/confirm · none · opp | 1709 / +1,08 | 594 / +0,48 | +2,1 | +0,86 | 567 / +0,23 | +0,51 | 270 | 33 | ❌ |
| long | 2h protnutí 2 průměrů ema/10/30/confirm · none · opp | 2543 / +0,51 | 916 / +0,30 | +2,5 | +0,38 | 857 / +0,12 | +0,06 | 191 | 49 | ❌ |
| long | 4h protnutí 2 průměrů sma/5/30/cross · none · opp | 1771 / +0,57 | 639 / +0,26 | +2,4 | +0,42 | 588 / +0,07 | +0,12 | 137 | 34 | ❌ |
| long | 2h protnutí 2 průměrů ema/40/150/confirm · none · opp | 589 / +2,55 | 225 / +1,68 | +2,0 | +2,33 | 197 / +0,09 | +0,10 | 142 | 11 | ❌ |
| long | 2h protnutí 2 průměrů ema/10/30/cross · none · opp | 2538 / +0,51 | 916 / +0,30 | +2,5 | +0,39 | 857 / +0,12 | +0,17 | 191 | 49 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/60/cross · none · opp | 2311 / +0,65 | 813 / +0,33 | +2,5 | +0,55 | 753 / +0,11 | +0,10 | 210 | 44 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/150/confirm · none · opp | 2011 / +1,01 | 696 / +0,43 | +2,2 | +0,74 | 665 / +0,16 | +0,32 | 302 | 38 | ❌ |
| long | 2h protnutí 2 průměrů sma/10/200/confirm · none · opp | 851 / +1,89 | 292 / +1,27 | +2,4 | +1,60 | 278 / +0,02 | +0,17 | 194 | 16 | ❌ |
| long | 1h protnutí 2 průměrů sma/20/150/confirm · none · opp | 1581 / +1,23 | 530 / +0,61 | +2,2 | +0,90 | 511 / +0,20 | +0,24 | 288 | 30 | ❌ |
| long | 4h MACD 19/39/9/signal · none · opp | 2222 / +0,35 | 767 / +0,24 | +3,1 | +0,30 | 733 / +0,05 | +0,14 | 152 | 42 | ❌ |
| long | 1h protnutí 2 průměrů sma/10/30/confirm · d50 · opp | 2938 / +0,36 | 963 / +0,08 | +1,1 | +0,09 | 679 / +0,18 | +0,32 | 124 | 52 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/200/pullback · none · opp | 832 / +1,73 | 277 / +1,34 | +2,1 | +1,79 | 254 / +0,19 | +0,09 | 139 | 16 | ❌ |
| long | 2h MACD 12/26/9/zero · none · opp | 2512 / +0,50 | 916 / +0,28 | +2,4 | +0,32 | 838 / +0,12 | +0,11 | 187 | 49 | ❌ |
| long | 4h protnutí 2 průměrů sma/10/60/confirm · none · opp | 837 / +1,26 | 298 / +0,77 | +2,0 | +1,22 | 289 / +0,05 | +0,07 | 110 | 16 | ❌ |
| long | 1h protnutí 2 průměrů ema/40/150/confirm · none · opp | 1297 / +1,37 | 464 / +0,55 | +1,8 | +1,10 | 407 / +0,10 | +0,47 | 279 | 25 | ❌ |
| long | 4h protnutí 2 průměrů sma/5/30/confirm · none · opp | 1686 / +0,59 | 600 / +0,28 | +2,5 | +0,39 | 555 / +0,08 | +0,10 | 134 | 32 | ❌ |
| long | 1h protnutí 2 průměrů sma/50/200/confirm · none · opp | 1028 / +1,82 | 346 / +0,71 | +1,8 | +1,37 | 312 / +0,29 | +0,60 | 236 | 19 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/60/confirm · none · opp | 2201 / +0,67 | 775 / +0,33 | +2,4 | +0,55 | 709 / +0,12 | +0,14 | 202 | 42 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/50/cross · none · opp | 2572 / +0,56 | 905 / +0,26 | +2,5 | +0,34 | 828 / +0,10 | +0,19 | 213 | 49 | ❌ |
| long | 2h protnutí 2 průměrů sma/10/60/cross · none · opp | 1777 / +0,82 | 631 / +0,40 | +2,3 | +0,77 | 592 / +0,08 | +0,17 | 210 | 34 | ❌ |
| long | 2h protnutí 2 průměrů sma/10/60/confirm · none · opp | 1699 / +0,85 | 592 / +0,44 | +2,4 | +0,77 | 557 / +0,11 | +0,12 | 201 | 32 | ❌ |
| long | 4h protnutí 2 průměrů ema/20/30/cross · none · opp | 925 / +1,15 | 338 / +0,69 | +2,0 | +1,12 | 312 / +0,01 | +0,07 | 139 | 18 | ❌ |
| long | 12h MACD 19/39/9/signal · none · opp | 698 / +0,78 | 240 / +0,65 | +2,9 | +0,59 | 201 / +0,19 | +0,07 | 49 | 13 | ✅ |
| long | 1h protnutí 2 průměrů ema/50/60/cross · none · opp | 1621 / +1,27 | 582 / +0,56 | +2,2 | +0,86 | 560 / +0,18 | +0,43 | 288 | 31 | ❌ |
| long | 2h protnutí 2 průměrů sma/5/50/confirm · none · opp | 2445 / +0,59 | 859 / +0,27 | +2,5 | +0,37 | 790 / +0,11 | +0,14 | 210 | 47 | ❌ |
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
| short | 1h protnutí 2 průměrů sma/50/60/pullback · d50 · trail | 1481 / +0,18 | 597 / -0,11 | -1,7 | +0,09 | 565 / +0,02 | +0,11 | 121 | 30 | ❌ |
| short | 4h průraz s objemem 20/2.5 · d50 · target | 324 / +0,23 | 169 / +0,02 | +0,2 | +0,01 | 151 / -0,01 | +0,14 | 29 | 7 | ❌ |
| short | 4h průraz s objemem 55/2.5 · d200 · target | 219 / +0,28 | 91 / +0,02 | +0,1 | +0,10 | 131 / +0,02 | +0,12 | 23 | 5 | ❌ |
| short | 2h Bollinger průraz 50/2.5 · d50 · target | 725 / +0,15 | 291 / +0,11 | +1,5 | +0,09 | 283 / +0,03 | +0,11 | 36 | 15 | ❌ |
| short | 4h MACD 19/39/9/signal · d50 · opp_stop | 916 / +0,20 | 362 / +0,07 | +0,9 | +0,02 | 427 / -0,07 | +0,13 | 82 | 19 | ❌ |
| short | 6h MACD 19/39/9/signal · d50 · opp | 585 / +0,20 | 224 / +0,07 | +0,8 | +0,01 | 278 / +0,01 | +0,08 | 45 | 12 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/100/confirm · d50 · trail | 2117 / +0,13 | 869 / -0,02 | -0,3 | +0,09 | 843 / +0,02 | +0,11 | 97 | 44 | ❌ |
| short | 6h MACD 19/39/9/signal · d200 · opp_stop | 620 / +0,24 | 178 / +0,04 | +0,4 | +0,06 | 339 / +0,07 | +0,12 | 57 | 13 | ❌ |
| short | 1h protnutí 2 průměrů sma/40/50/pullback · d50 · trail | 1678 / +0,15 | 626 / -0,07 | -1,0 | +0,05 | 614 / +0,08 | +0,07 | 112 | 33 | ❌ |
| short | 6h protnutí 2 průměrů ema/50/100/cross · none · target | 178 / +0,27 | 74 / -0,16 | -1,2 | +0,04 | 57 / +0,27 | +0,21 | 26 | 4 | ❌ |
| short | 1h Bollinger průraz 50/2.0 · d50 · trail | 1557 / +0,16 | 656 / +0,07 | +0,9 | +0,04 | 661 / +0,06 | +0,07 | 72 | 33 | ❌ |
| short | 2h protnutí 2 průměrů ema/30/200/cross · none · target | 482 / +0,17 | 202 / +0,21 | +2,5 | +0,10 | 174 / +0,04 | +0,08 | 30 | 10 | ❌ |
| short | 1h protnutí 2 průměrů ema/20/100/cross · d50 · opp_stop | 785 / +0,46 | 327 / +0,15 | +0,9 | +0,02 | 371 / +0,09 | +0,49 | 116 | 17 | ❌ |
| short | 12h protnutí 2 průměrů ema/5/150/cross · none · trail | 162 / +0,37 | 86 / -0,24 | -2,2 | +0,10 | 51 / +0,97 | +0,43 | 33 | 3 | ❌ |
| short | 4h Bollinger průraz 50/2.5 · d200 · target | 302 / +0,21 | 98 / +0,16 | +1,3 | -0,01 | 140 / +0,20 | +0,29 | 23 | 6 | ❌ |
| short | 1h protnutí 2 průměrů sma/30/50/pullback · d50 · trail | 1797 / +0,14 | 706 / +0,04 | +0,6 | +0,07 | 723 / +0,07 | +0,04 | 77 | 37 | ❌ |
| short | 1h Bollinger průraz 50/2.0 · d200 · trail | 1419 / +0,15 | 469 / +0,07 | +0,9 | +0,06 | 725 / +0,02 | +0,06 | 77 | 30 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/60/confirm · d50 · trail | 2279 / +0,12 | 902 / -0,01 | -0,2 | +0,10 | 871 / +0,10 | +0,10 | 76 | 46 | ❌ |
| short | 2h protnutí 2 průměrů sma/20/30/pullback · d50 · trail | 1045 / +0,17 | 373 / -0,02 | -0,2 | +0,05 | 385 / +0,10 | +0,18 | 58 | 21 | ❌ |
| short | 1h protnutí 2 průměrů ema/50/60/confirm · d50 · trail | 2341 / +0,12 | 963 / +0,02 | +0,3 | +0,09 | 1014 / +0,04 | +0,11 | 108 | 49 | ❌ |
| short | 6h MACD 12/26/9/signal · d200 · opp_stop | 790 / +0,17 | 244 / +0,04 | +0,5 | +0,02 | 438 / +0,00 | +0,12 | 69 | 17 | ❌ |
| short | 1h cena × průměr ema/50 · d50 · trail | 2984 / +0,10 | 1190 / +0,04 | +0,7 | +0,07 | 1296 / +0,07 | +0,07 | 114 | 62 | ❌ |
| short | 2h protnutí 2 průměrů ema/40/150/cross · none · target | 496 / +0,15 | 203 / +0,09 | +1,1 | +0,09 | 187 / -0,03 | +0,12 | 38 | 10 | ❌ |
| short | 6h protnutí 2 průměrů ema/20/200/cross · none · target | 178 / +0,25 | 91 / -0,06 | -0,5 | +0,14 | 62 / +0,02 | +0,19 | 25 | 4 | ❌ |
| short | 2h protnutí 2 průměrů sma/5/60/pullback · d50 · trail | 1551 / +0,13 | 637 / -0,01 | -0,1 | +0,11 | 677 / -0,03 | +0,13 | 124 | 33 | ❌ |
| short | 2h protnutí 2 průměrů sma/40/50/cross · d50 · opp_stop | 995 / +0,24 | 407 / -0,01 | -0,1 | -0,01 | 413 / +0,10 | +0,03 | 87 | 21 | ❌ |
| short | 6h MACD 12/26/9/signal · d50 · opp | 755 / +0,14 | 310 / +0,00 | +0,0 | +0,04 | 366 / -0,05 | +0,05 | 67 | 16 | ❌ |
| short | 2h protnutí 2 průměrů sma/10/60/pullback · d50 · opp | 786 / +0,25 | 312 / -0,10 | -1,0 | -0,02 | 321 / +0,06 | +0,28 | 100 | 16 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/100/pullback · d50 · trail | 1638 / +0,14 | 673 / -0,10 | -1,6 | +0,11 | 622 / -0,02 | +0,04 | 135 | 33 | ❌ |
| short | 6h Supertrend 20/3.0 · d200 · opp | 198 / +0,42 | 70 / +0,21 | +1,3 | -0,36 | 115 / +0,15 | +0,56 | 48 | 4 | ❌ |
| short | 1h protnutí 2 průměrů ema/50/60/confirm · d50 · opp | 915 / +0,35 | 385 / -0,13 | -0,9 | +0,02 | 404 / +0,04 | +0,27 | 169 | 19 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/150/cross · d50 · opp_stop | 551 / +0,52 | 233 / +0,14 | +0,7 | -0,01 | 250 / -0,29 | +0,40 | 115 | 12 | ❌ |
| short | 12h MACD 5/35/5/signal · d200 · opp_stop | 652 / +0,13 | 198 / +0,05 | +0,7 | +0,05 | 360 / +0,04 | +0,08 | 39 | 14 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/60/pullback · d50 · trail | 2032 / +0,12 | 849 / -0,02 | -0,3 | +0,12 | 830 / -0,00 | +0,11 | 106 | 42 | ❌ |
| short | 6h protnutí 2 průměrů ema/30/150/cross · none · target | 178 / +0,24 | 84 / +0,03 | +0,2 | +0,22 | 58 / +0,22 | +0,27 | 20 | 4 | ❌ |
| short | 1h protnutí 2 průměrů sma/50/100/pullback · none · trail | 2776 / +0,10 | 1029 / -0,04 | -0,7 | +0,10 | 896 / +0,04 | +0,06 | 152 | 53 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/50/confirm · d50 · opp_stop | 1745 / +0,23 | 722 / -0,02 | -0,2 | +0,02 | 734 / +0,15 | +0,16 | 177 | 36 | ❌ |
| short | 1h protnutí 2 průměrů sma/30/100/pullback · d50 · trail | 2023 / +0,12 | 816 / -0,03 | -0,4 | +0,05 | 849 / -0,07 | +0,08 | 169 | 42 | ❌ |
| short | 6h protnutí 2 průměrů ema/30/100/cross · d50 · target | 155 / +0,26 | 65 / +0,11 | +0,8 | +0,20 | 60 / -0,14 | +0,13 | 21 | 3 | ❌ |
| short | 4h průraz s objemem 20/1.5 · none · target | 1021 / +0,10 | 423 / +0,09 | +1,6 | +0,01 | 366 / -0,00 | +0,08 | 57 | 21 | ❌ |
| short | 1h protnutí 2 průměrů ema/30/200/cross · d50 · opp_stop | 459 / +0,61 | 211 / +0,25 | +1,1 | -0,13 | 239 / -0,46 | +0,29 | 125 | 10 | ❌ |
| short | 2h protnutí 2 průměrů sma/40/50/confirm · d50 · trail | 1240 / +0,14 | 500 / +0,03 | +0,4 | +0,08 | 551 / -0,00 | +0,19 | 90 | 26 | ❌ |
| short | 4h Donchian průraz 20 · d200 · target | 697 / +0,12 | 256 / +0,10 | +1,2 | -0,02 | 334 / +0,04 | +0,13 | 50 | 15 | ❌ |

## 5. Všechny kombinace, které splní kritéria (bez pořadí v IS) – kandidáti, ne důkaz

Splní je **209** z 33840 způsobilých kombinací. Čistou náhodou by to bylo řádově 25 (OOS i HOLDOUT nad p95 ≈ 0,25 %, k tomu t ≥ 2 a kladné IS). Kombinace v rámci rodiny jsou si podobné, takže skutečně nezávislých nálezů je méně.

| Směr | Kombinace | IS Ø R | OOS n / Ø R / t | HOLDOUT n / Ø R | Max. propad R | Obch./měs. | Ø % na obchod (OOS) |
|---|---|---|---|---|---|---|---|
| short | 6h Supertrend 10/3.0 · none · target | +0,03 | 201 / +0,36 / +4,1 | 168 / +0,21 | 50 | 10 | +1,85 |
| short | 6h Supertrend 10/3.0 · d200 · target | +0,14 | 71 / +0,58 / +4,1 | 109 / +0,20 | 19 | 4 | +3,68 |
| short | 6h Supertrend 10/3.0 · d50 · target | +0,09 | 80 / +0,52 / +3,9 | 90 / +0,20 | 24 | 4 | +3,45 |
| short | 2h Keltner průraz 2.5 · none · target | +0,04 | 430 / +0,20 / +3,5 | 382 / +0,11 | 54 | 22 | +0,44 |
| long | 1h Bollinger průraz 50/2.5 · none · opp_stop | +0,40 | 733 / +0,57 / +3,2 | 687 / +0,37 | 135 | 43 | +0,78 |
| long | 2h RSI momentum 60 · none · opp | +0,32 | 927 / +0,24 / +3,2 | 856 / +0,12 | 156 | 51 | +0,67 |
| long | 1h Bollinger průraz 50/2.5 · none · opp | +0,43 | 645 / +0,49 / +3,1 | 596 / +0,28 | 141 | 37 | +0,91 |
| long | 2h RSI momentum 55 · none · opp_stop | +0,24 | 1524 / +0,19 / +3,0 | 1416 / +0,08 | 226 | 86 | +0,37 |
| long | 1h Bollinger průraz 50/2.0 · none · opp | +0,37 | 906 / +0,37 / +3,0 | 827 / +0,16 | 182 | 50 | +0,67 |
| long | 2h RSI momentum 60 · none · opp_stop | +0,37 | 984 / +0,28 / +3,0 | 902 / +0,18 | 169 | 55 | +0,56 |
| short | 2h protnutí 2 průměrů sma/20/50/cross · none · target | +0,03 | 561 / +0,15 / +2,9 | 517 / +0,11 | 49 | 31 | +0,36 |
| long | 12h MACD 19/39/9/signal · none · opp | +0,78 | 240 / +0,65 / +2,9 | 201 / +0,19 | 49 | 13 | +4,18 |
| long | 2h protnutí 2 průměrů ema/5/50/cross · none · trail | +0,18 | 797 / +0,22 / +2,9 | 762 / +0,12 | 111 | 43 | +0,50 |
| short | 1h protnutí 2 průměrů sma/50/100/cross · none · trail | +0,02 | 575 / +0,23 / +2,9 | 521 / +0,13 | 103 | 31 | +0,37 |
| long | 1h protnutí 2 průměrů sma/5/60/pullback · d50 · opp | +0,49 | 608 / +0,38 / +2,9 | 436 / +0,32 | 117 | 34 | +0,93 |
| long | 1h Bollinger průraz 50/2.0 · none · opp_stop | +0,36 | 1067 / +0,38 / +2,9 | 996 / +0,19 | 201 | 61 | +0,48 |
| long | 1h MACD 19/39/9/zero · none · opp | +0,49 | 1147 / +0,34 / +2,9 | 1098 / +0,10 | 266 | 64 | +0,61 |
| short | 2h protnutí 2 průměrů ema/40/200/cross · none · target | +0,08 | 175 / +0,26 / +2,8 | 155 / +0,14 | 18 | 9 | +0,93 |
| short | 4h Supertrend 10/3.0 · d50 · trail | +0,06 | 116 / +0,40 / +2,8 | 155 / +0,27 | 36 | 7 | +1,71 |
| long | 1h průraz s objemem 55/1.5 · none · opp | +0,78 | 553 / +0,57 / +2,7 | 465 / +0,52 | 195 | 29 | +0,95 |
| long | 1h protnutí 2 průměrů sma/5/60/cross · none · opp | +0,29 | 1625 / +0,23 / +2,7 | 1516 / +0,05 | 268 | 93 | +0,35 |
| long | 1h průraz s objemem 55/2.5 · none · opp | +1,06 | 434 / +0,65 / +2,7 | 377 / +0,58 | 125 | 22 | +1,18 |
| long | 2h MACD 19/39/9/signal · none · opp | +0,15 | 1528 / +0,12 / +2,7 | 1396 / +0,07 | 174 | 84 | +0,42 |
| long | 2h protnutí 2 průměrů ema/5/30/confirm · none · opp | +0,33 | 1267 / +0,20 / +2,7 | 1177 / +0,06 | 207 | 69 | +0,49 |
| long | 1h Supertrend 20/3.0 · none · opp | +0,27 | 1223 / +0,23 / +2,7 | 1145 / +0,10 | 209 | 67 | +0,47 |
| long | 2h Bollinger průraz 50/2.0 · none · opp | +0,77 | 448 / +0,46 / +2,6 | 384 / +0,40 | 120 | 24 | +1,21 |
| short | 6h protnutí 2 průměrů ema/10/50/cross · none · target | +0,06 | 207 / +0,22 / +2,6 | 188 / +0,14 | 37 | 10 | +1,58 |
| long | 2h protnutí 2 průměrů sma/5/150/cross · none · trail | +0,20 | 434 / +0,28 / +2,6 | 400 / +0,29 | 60 | 23 | +0,69 |
| long | 12h MACD 19/39/9/signal · none · opp_stop | +0,89 | 240 / +0,76 / +2,6 | 201 / +0,25 | 44 | 13 | +3,72 |
| long | 6h protnutí 2 průměrů ema/50/60/cross · none · target | +0,06 | 88 / +0,34 / +2,6 | 84 / +0,40 | 29 | 5 | +1,80 |
| long | 1h Donchian průraz 55 · none · opp | +0,75 | 607 / +0,51 / +2,6 | 523 / +0,40 | 205 | 32 | +0,81 |
| long | 6h Bollinger průraz 50/2.5 · none · target | +0,20 | 170 / +0,25 / +2,6 | 135 / +0,07 | 35 | 10 | +1,41 |
| long | 1h Bollinger průraz 50/2.5 · none · trail | +0,20 | 738 / +0,22 / +2,5 | 681 / +0,16 | 94 | 43 | +0,44 |
| long | 6h RSI momentum 60 · none · opp | +0,77 | 310 / +0,52 / +2,5 | 283 / +0,19 | 77 | 17 | +2,28 |
| long | 6h Bollinger průraz 20/2.0 · none · opp | +0,61 | 322 / +0,42 / +2,5 | 262 / +0,32 | 60 | 17 | +1,69 |
| short | 1h protnutí 2 průměrů sma/20/30/pullback · d200 · trail | +0,01 | 537 / +0,20 / +2,5 | 838 / +0,06 | 82 | 36 | +0,25 |
| long | 6h RSI momentum 60 · none · opp_stop | +0,87 | 325 / +0,64 / +2,5 | 302 / +0,27 | 93 | 18 | +2,13 |
| long | 4h Bollinger průraz 20/2.0 · none · opp | +0,45 | 487 / +0,25 / +2,5 | 412 / +0,18 | 84 | 26 | +0,90 |
| short | 2h protnutí 2 průměrů sma/30/50/cross · none · target | +0,04 | 553 / +0,13 / +2,5 | 521 / +0,08 | 62 | 31 | +0,44 |
| long | 2h protnutí 2 průměrů ema/20/30/cross · none · trail | +0,13 | 609 / +0,21 / +2,5 | 580 / +0,10 | 120 | 33 | +0,44 |

Podle rodiny a timeframu: protnutí 2 průměrů 2h long: 24; protnutí 2 průměrů 1h long: 13; protnutí 2 průměrů 6h long: 12; Bollinger průraz 2h long: 12; protnutí 2 průměrů 12h long: 10; protnutí 2 průměrů 4h long: 10; Bollinger průraz 6h long: 9; Bollinger průraz 1h long: 8; Bollinger průraz 4h long: 8; protnutí 2 průměrů 1h short: 8; Keltner průraz 6h long: 7; průraz s objemem 1h long: 6; Bollinger průraz 12h long: 6; Donchian průraz 1h long: 6; MACD 2h long: 5.

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