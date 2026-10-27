# Mřížka klouzavých průměrů – všechny kombinace (27. 10. 2026)

Otázka: dá se short (a long) vést podle protnutí dvou klouzavých průměrů, např. MA 30 × MA 60 na 4H, lépe než dnešní denní strategie s filtrem EMA 200? Metoda stanovená předem je v hlavičce skriptu `research/experiments/ma_grid.py`; nic se po spuštění neladilo.

- **27 648 kombinací** (6 timeframů × SMA/EMA × 32 dvojic délek × 3 signály × 3 filtry × 4 výstupy × long/short), 8 mincí, hodinová data OKX; BTC od 01/2019, ETH od 01/2019, SOL od 09/2020, XRP od 01/2019, ADA od 01/2019, LINK od 01/2019, AVAX od 09/2020, DOGE od 07/2019.
- Náklady 0,15 % na stranu, funding u shortů nezapočten. R = výsledek / riziko (u výstupu „opp“ 2 ATR).
- IS do 12/2023, OOS 1/2024–6/2025, HOLDOUT 7/2025–dnes. Výpočet trval 23 min.

## 1. Celá rodina: mají průměry vůbec nějakou výhodu?

Podíl kombinací s kladným Ø R a medián Ø R; „náhoda“ = medián Ø R náhodných vstupů, které má každá kombinace vlastní (stejná mince, směr, filtr, výstup i opačný signál, podobný počet obchodů, 10 opakování).

| Směr | TF | Kombinací | IS > 0 | OOS > 0 | HOLDOUT > 0 | Medián OOS R | Náhoda OOS R | Medián HOLDOUT R | Náhoda HOLDOUT R | Obchodů/měs. (medián) |
|---|---|---|---|---|---|---|---|---|---|---|
| short | 1h | 2304 | 15% | 11% | 4% | -0,09 | -0,13 | -0,13 | -0,12 | 39 |
| long | 1h | 2304 | 69% | 48% | 38% | -0,02 | -0,11 | -0,05 | -0,07 | 37 |
| short | 2h | 2304 | 29% | 18% | 35% | -0,11 | -0,11 | -0,05 | -0,02 | 20 |
| long | 2h | 2304 | 78% | 60% | 49% | +0,08 | -0,03 | -0,00 | -0,07 | 18 |
| short | 4h | 2304 | 38% | 18% | 67% | -0,14 | -0,16 | +0,08 | +0,09 | 10 |
| long | 4h | 2304 | 90% | 71% | 58% | +0,18 | +0,07 | +0,05 | -0,07 | 9 |
| short | 6h | 2304 | 48% | 17% | 79% | -0,16 | -0,21 | +0,16 | +0,08 | 7 |
| long | 6h | 2304 | 93% | 76% | 50% | +0,50 | +0,30 | -0,00 | -0,08 | 6 |
| short | 12h | 2304 | 35% | 18% | 84% | -0,23 | -0,27 | +0,32 | +0,20 | 3 |
| long | 12h | 2304 | 95% | 73% | 54% | +0,51 | +0,26 | +0,04 | -0,13 | 3 |
| short | 1d | 2304 | 25% | 8% | 89% | -0,33 | -0,34 | +0,53 | +0,18 | 2 |
| long | 1d | 2304 | 93% | 63% | 34% | +0,29 | +0,07 | -0,15 | -0,22 | 2 |

## 2. Co rozhoduje (medián OOS R podle jedné volby, ostatní volby smíchané)

**exit:** opp: short -0,36, long +0,82; opp_stop: short -0,32, long +0,55; target: short -0,05, long -0,13; trail: short -0,10, long +0,11  
**filter:** d200: short -0,23, long +0,18; d50: short -0,15, long +0,17; none: short -0,09, long +0,22  
**signal:** confirm: short -0,15, long +0,28; cross: short -0,13, long +0,25; pullback: short -0,16, long +0,09  
**ma:** ema: short -0,15, long +0,19; sma: short -0,15, long +0,19  

## 3. Výběr podle předem stanoveného pravidla (25 nejlepších podle IS t-statistiky na směr)

| Směr | Kombinace | IS n / Ø R | OOS n / Ø R ± CI | OOS t | Náhoda OOS p95 | HOLDOUT n / Ø R | Náhoda HOLD p95 | Max. propad R | Prošlo |
|---|---|---|---|---|---|---|---|---|---|
| long | 1h SMA 30/200 · confirm · none · opp | 1178 / +1,56 | 420 / +0,51 ± 0,63 | +1,6 | +0,55 | 372 / +0,04 | +0,40 | 276 | ❌ |
| long | 1h SMA 40/200 · confirm · none · opp | 1071 / +1,72 | 379 / +0,73 ± 0,76 | +1,9 | +1,03 | 329 / +0,04 | +0,75 | 273 | ❌ |
| long | 2h SMA 20/200 · confirm · none · opp | 633 / +2,31 | 229 / +1,62 ± 1,52 | +2,1 | +2,23 | 205 / -0,28 | -0,36 | 207 | ❌ |
| long | 4h SMA 10/100 · confirm · none · opp | 558 / +1,90 | 209 / +1,46 ± 1,33 | +2,1 | +2,47 | 191 / -0,11 | -0,24 | 131 | ❌ |
| long | 1h SMA 30/200 · confirm · d50 · opp | 740 / +2,00 | 254 / +0,50 ± 0,97 | +1,0 | +0,83 | 178 / +0,74 | +1,30 | 125 | ❌ |
| long | 2h EMA 40/150 · confirm · none · opp | 589 / +2,48 | 225 / +1,61 ± 1,68 | +1,9 | +2,17 | 197 / +0,01 | +0,21 | 155 | ❌ |
| long | 4h SMA 10/100 · cross · none · opp | 596 / +1,77 | 216 / +1,43 ± 1,29 | +2,2 | +2,12 | 199 / -0,09 | -0,16 | 129 | ❌ |
| long | 2h SMA 5/200 · confirm · none · opp | 1075 / +1,51 | 361 / +0,98 ± 0,82 | +2,4 | +1,53 | 355 / +0,05 | -0,11 | 203 | ❌ |
| long | 1h SMA 40/200 · confirm · d50 · opp | 681 / +2,17 | 228 / +0,65 ± 1,12 | +1,1 | +0,96 | 156 / +1,30 | +1,26 | 112 | ❌ |
| long | 1h EMA 50/200 · confirm · none · opp | 1029 / +1,76 | 357 / +0,58 ± 0,68 | +1,7 | +0,50 | 330 / -0,07 | +0,49 | 323 | ❌ |
| long | 2h SMA 10/200 · confirm · none · opp | 851 / +1,82 | 292 / +1,20 ± 1,03 | +2,3 | +1,50 | 278 / -0,07 | -0,10 | 214 | ❌ |
| long | 2h SMA 5/200 · pullback · none · opp | 832 / +1,66 | 277 / +1,26 ± 1,24 | +2,0 | +1,74 | 254 / +0,11 | -0,07 | 156 | ❌ |
| long | 4h SMA 10/60 · confirm · none · opp | 837 / +1,21 | 298 / +0,72 ± 0,76 | +1,9 | +1,18 | 289 / -0,01 | +0,14 | 122 | ❌ |
| long | 2h EMA 30/150 · confirm · none · opp | 658 / +2,32 | 248 / +1,23 ± 1,31 | +1,8 | +1,84 | 224 / +0,11 | -0,14 | 172 | ❌ |
| long | 1h EMA 40/200 · confirm · none · opp | 1125 / +1,54 | 400 / +0,54 ± 0,62 | +1,7 | +0,90 | 360 / +0,02 | +0,58 | 314 | ❌ |
| long | 4h EMA 10/60 · confirm · none · opp | 846 / +1,29 | 313 / +0,65 ± 0,68 | +1,9 | +1,17 | 289 / +0,04 | +0,02 | 138 | ❌ |
| long | 4h EMA 10/60 · cross · none · opp | 844 / +1,29 | 313 / +0,65 ± 0,68 | +1,9 | +1,08 | 289 / +0,04 | -0,12 | 138 | ❌ |
| long | 4h EMA 20/30 · cross · none · opp | 925 / +1,10 | 338 / +0,65 ± 0,69 | +1,8 | +1,14 | 312 / -0,05 | +0,14 | 152 | ❌ |
| long | 2h EMA 20/200 · confirm · none · opp | 675 / +2,25 | 268 / +1,16 ± 1,18 | +1,9 | +1,81 | 216 / +0,20 | -0,19 | 144 | ❌ |
| long | 2h EMA 50/150 · confirm · none · opp | 541 / +2,50 | 207 / +1,51 ± 1,70 | +1,7 | +2,02 | 170 / +0,10 | -0,09 | 132 | ❌ |
| long | 2h SMA 30/200 · confirm · none · opp | 572 / +2,33 | 203 / +1,62 ± 1,62 | +2,0 | +1,97 | 172 / -0,13 | +0,13 | 186 | ❌ |
| long | 1h SMA 20/200 · confirm · none · opp | 1381 / +1,26 | 479 / +0,41 ± 0,56 | +1,5 | +1,06 | 435 / -0,01 | +0,24 | 327 | ❌ |
| long | 4h EMA 20/30 · confirm · none · opp | 929 / +1,09 | 338 / +0,65 ± 0,69 | +1,8 | +1,03 | 312 / -0,05 | +0,02 | 152 | ❌ |
| long | 4h SMA 10/60 · cross · none · opp | 896 / +1,11 | 317 / +0,66 ± 0,72 | +1,8 | +1,01 | 297 / +0,01 | +0,00 | 117 | ❌ |
| long | 6h EMA 10/30 · cross · none · opp | 837 / +1,05 | 306 / +0,59 ± 0,58 | +2,0 | +0,97 | 293 / -0,05 | -0,14 | 115 | ❌ |
| short | 12h EMA 5/150 · cross · none · trail | 162 / +0,35 | 86 / -0,26 ± 0,21 | -2,4 | +0,06 | 51 / +0,93 | +0,37 | 35 | ❌ |
| short | 6h EMA 50/100 · cross · none · target | 178 / +0,24 | 74 / -0,19 ± 0,26 | -1,5 | +0,10 | 57 / +0,22 | +0,01 | 29 | ❌ |
| short | 6h EMA 20/200 · cross · none · target | 178 / +0,21 | 91 / -0,10 ± 0,24 | -0,8 | +0,08 | 62 / -0,03 | +0,26 | 28 | ❌ |
| short | 6h EMA 30/150 · cross · none · target | 178 / +0,21 | 84 / -0,01 ± 0,25 | -0,0 | +0,16 | 58 / +0,18 | +0,12 | 22 | ❌ |
| short | 12h EMA 10/100 · cross · none · trail | 174 / +0,26 | 87 / -0,17 ± 0,21 | -1,6 | +0,02 | 61 / +0,69 | +0,45 | 36 | ❌ |
| short | 6h EMA 30/100 · cross · d50 · target | 155 / +0,23 | 65 / +0,08 ± 0,29 | +0,5 | -0,02 | 60 / -0,18 | +0,17 | 25 | ❌ |
| short | 12h EMA 30/50 · cross · none · target | 161 / +0,21 | 67 / +0,15 ± 0,29 | +1,0 | +0,26 | 53 / +0,16 | +0,14 | 19 | ❌ |
| short | 12h EMA 10/100 · cross · none · target | 167 / +0,20 | 80 / +0,06 ± 0,26 | +0,4 | +0,25 | 59 / +0,14 | +0,21 | 23 | ❌ |
| short | 1h EMA 20/100 · cross · d50 · opp_stop | 785 / +0,31 | 327 / +0,01 ± 0,32 | +0,1 | -0,17 | 371 / -0,06 | +0,21 | 154 | ❌ |
| short | 1h EMA 20/200 · cross · d200 · opp | 574 / +0,35 | 183 / -0,06 ± 0,41 | -0,3 | -0,19 | 330 / -0,40 | +0,16 | 189 | ❌ |
| short | 12h EMA 20/60 · cross · none · target | 170 / +0,18 | 79 / -0,02 ± 0,26 | -0,2 | +0,15 | 60 / +0,10 | +0,14 | 20 | ❌ |
| short | 1h EMA 30/200 · cross · d50 · opp_stop | 459 / +0,46 | 211 / +0,12 ± 0,46 | +0,5 | -0,11 | 239 / -0,62 | +0,06 | 167 | ❌ |
| short | 2h SMA 10/60 · pullback · d50 · opp | 786 / +0,18 | 312 / -0,17 ± 0,20 | -1,6 | -0,06 | 321 / -0,03 | +0,21 | 134 | ❌ |
| short | 1h EMA 30/150 · cross · d50 · opp_stop | 551 / +0,38 | 233 / +0,01 ± 0,41 | +0,0 | -0,12 | 250 / -0,44 | +0,39 | 144 | ❌ |
| short | 6h EMA 30/150 · cross · d50 · target | 152 / +0,19 | 71 / -0,08 ± 0,27 | -0,6 | -0,02 | 50 / +0,21 | +0,11 | 22 | ❌ |
| short | 1d EMA 5/50 · cross · none · trail | 151 / +0,22 | 77 / -0,24 ± 0,20 | -2,3 | -0,01 | 56 / +0,54 | +0,39 | 32 | ❌ |
| short | 12h SMA 50/60 · cross · d50 · trail | 152 / +0,26 | 65 / -0,22 ± 0,28 | -1,6 | -0,07 | 62 / +0,32 | +0,27 | 22 | ❌ |
| short | 12h SMA 10/60 · cross · d50 · trail | 160 / +0,23 | 64 / -0,14 ± 0,26 | -1,0 | -0,02 | 61 / +0,22 | +0,26 | 31 | ❌ |
| short | 12h EMA 5/150 · cross · none · target | 156 / +0,18 | 82 / -0,03 ± 0,26 | -0,2 | +0,13 | 50 / +0,12 | +0,21 | 23 | ❌ |
| short | 12h EMA 5/100 · cross · none · trail | 227 / +0,19 | 108 / -0,14 ± 0,19 | -1,4 | +0,06 | 71 / +0,66 | +0,36 | 35 | ❌ |
| short | 6h EMA 20/60 · cross · d200 · target | 151 / +0,19 | 55 / -0,12 ± 0,32 | -0,8 | -0,01 | 80 / -0,10 | +0,21 | 27 | ❌ |
| short | 6h EMA 40/60 · cross · d50 · target | 159 / +0,18 | 72 / +0,14 ± 0,28 | +1,0 | -0,01 | 64 / -0,22 | +0,12 | 20 | ❌ |
| short | 2h EMA 30/200 · cross · none · target | 482 / +0,11 | 202 / +0,14 ± 0,16 | +1,7 | +0,00 | 174 / -0,05 | +0,04 | 36 | ❌ |
| short | 1h EMA 50/60 · confirm · d50 · opp | 915 / +0,24 | 385 / -0,23 ± 0,28 | -1,6 | +0,05 | 404 / -0,07 | +0,24 | 246 | ❌ |
| short | 12h EMA 30/50 · cross · none · trail | 161 / +0,20 | 68 / -0,09 ± 0,25 | -0,7 | +0,13 | 54 / +0,82 | +0,47 | 26 | ❌ |

## 4. Vaše hypotéza: MA 30 × MA 60 na 4H

| Průměr | Směr | Signál | Filtr | Výstup | IS n / Ø R | OOS n / Ø R | HOLDOUT n / Ø R | Obchodů/měs. |
|---|---|---|---|---|---|---|---|---|
| EMA | long | confirm | d200 | opp | 250 / +2,53 | 126 / +0,95 | 54 / -0,66 | 5 |
| EMA | long | confirm | d200 | opp_stop | 370 / +2,03 | 183 / +0,63 | 94 / -0,20 | 7 |
| EMA | long | confirm | d200 | target | 608 / -0,02 | 271 / -0,04 | 136 / -0,14 | 12 |
| EMA | long | confirm | d200 | trail | 635 / +0,20 | 279 / +0,15 | 147 / +0,06 | 12 |
| EMA | long | confirm | d50 | opp | 323 / +2,40 | 131 / +0,99 | 84 / +0,54 | 6 |
| EMA | long | confirm | d50 | opp_stop | 467 / +2,06 | 192 / +0,76 | 125 / +0,48 | 9 |
| EMA | long | confirm | d50 | target | 773 / +0,00 | 263 / -0,14 | 195 / -0,13 | 14 |
| EMA | long | confirm | d50 | trail | 808 / +0,28 | 274 / +0,07 | 208 / +0,30 | 15 |
| EMA | long | confirm | none | opp | 487 / +2,50 | 197 / +1,28 | 163 / -0,05 | 10 |
| EMA | long | confirm | none | opp_stop | 718 / +1,95 | 273 / +1,05 | 251 / +0,13 | 14 |
| EMA | long | confirm | none | target | 1161 / -0,00 | 407 / -0,01 | 356 / -0,11 | 22 |
| EMA | long | confirm | none | trail | 1202 / +0,30 | 405 / +0,13 | 369 / +0,18 | 22 |
| EMA | long | cross | d200 | opp | 196 / +3,02 | 104 / +0,62 | 41 / -0,82 | 4 |
| EMA | long | cross | d200 | opp_stop | 196 / +2,49 | 104 / +0,29 | 41 / -0,68 | 4 |
| EMA | long | cross | d200 | target | 190 / +0,02 | 101 / -0,06 | 41 / +0,07 | 4 |
| EMA | long | cross | d200 | trail | 191 / +0,48 | 101 / +0,06 | 41 / -0,04 | 4 |
| EMA | long | cross | d50 | opp | 191 / +2,77 | 90 / +1,44 | 54 / +0,52 | 4 |
| EMA | long | cross | d50 | opp_stop | 191 / +2,50 | 90 / +1,88 | 54 / +0,45 | 4 |
| EMA | long | cross | d50 | target | 186 / +0,02 | 86 / -0,15 | 54 / +0,06 | 4 |
| EMA | long | cross | d50 | trail | 186 / +0,58 | 86 / +0,08 | 54 / +1,05 | 4 |
| EMA | long | cross | none | opp | 478 / +2,56 | 196 / +1,29 | 163 / -0,05 | 10 |
| EMA | long | cross | none | opp_stop | 478 / +1,97 | 196 / +1,52 | 163 / -0,30 | 10 |
| EMA | long | cross | none | target | 468 / +0,03 | 188 / +0,10 | 159 / -0,10 | 9 |
| EMA | long | cross | none | trail | 470 / +0,45 | 188 / +0,12 | 160 / +0,23 | 9 |
| EMA | long | pullback | d200 | opp | 206 / +1,65 | 84 / +0,88 | 47 / -0,16 | 4 |
| EMA | long | pullback | d200 | opp_stop | 294 / +1,28 | 125 / +0,83 | 69 / -0,09 | 6 |
| EMA | long | pullback | d200 | target | 475 / -0,07 | 188 / -0,07 | 102 / -0,16 | 9 |
| EMA | long | pullback | d200 | trail | 490 / +0,05 | 196 / +0,19 | 108 / +0,11 | 9 |
| EMA | long | pullback | d50 | opp | 277 / +1,73 | 89 / +0,51 | 72 / +0,01 | 5 |
| EMA | long | pullback | d50 | opp_stop | 378 / +1,59 | 138 / +0,46 | 98 / +0,13 | 7 |
| EMA | long | pullback | d50 | target | 640 / -0,01 | 190 / -0,18 | 149 / -0,17 | 11 |
| EMA | long | pullback | d50 | trail | 664 / +0,20 | 202 / +0,08 | 158 / +0,02 | 12 |
| EMA | long | pullback | none | opp | 370 / +1,60 | 115 / +0,62 | 108 / +0,09 | 7 |
| EMA | long | pullback | none | opp_stop | 500 / +1,50 | 169 / +0,48 | 149 / +0,23 | 9 |
| EMA | long | pullback | none | target | 817 / -0,02 | 249 / -0,12 | 227 / -0,03 | 15 |
| EMA | long | pullback | none | trail | 839 / +0,22 | 256 / +0,12 | 233 / +0,17 | 15 |
| SMA | long | confirm | d200 | opp | 311 / +1,81 | 150 / +0,40 | 66 / -0,20 | 6 |
| SMA | long | confirm | d200 | opp_stop | 429 / +1,55 | 226 / +0,22 | 101 / -0,05 | 9 |
| SMA | long | confirm | d200 | target | 553 / -0,03 | 266 / -0,05 | 114 / -0,10 | 11 |
| SMA | long | confirm | d200 | trail | 571 / +0,16 | 264 / +0,05 | 124 / +0,19 | 11 |
| SMA | long | confirm | d50 | opp | 395 / +1,71 | 147 / +0,76 | 95 / +0,53 | 7 |
| SMA | long | confirm | d50 | opp_stop | 565 / +1,36 | 218 / +0,45 | 133 / +0,58 | 10 |
| SMA | long | confirm | d50 | target | 715 / -0,01 | 251 / -0,11 | 165 / -0,07 | 13 |
| SMA | long | confirm | d50 | trail | 726 / +0,26 | 250 / +0,02 | 174 / +0,35 | 13 |
| SMA | long | confirm | none | opp | 648 / +1,47 | 236 / +0,51 | 183 / +0,24 | 12 |
| SMA | long | confirm | none | opp_stop | 951 / +1,16 | 349 / +0,34 | 277 / +0,24 | 18 |
| SMA | long | confirm | none | target | 1183 / +0,00 | 417 / -0,01 | 332 / +0,07 | 22 |
| SMA | long | confirm | none | trail | 1175 / +0,25 | 407 / +0,03 | 338 / +0,27 | 22 |
| SMA | long | cross | d200 | opp | 295 / +1,84 | 152 / +0,32 | 55 / -0,56 | 6 |
| SMA | long | cross | d200 | opp_stop | 295 / +1,75 | 152 / +0,32 | 55 / -0,21 | 6 |
| SMA | long | cross | d200 | target | 291 / -0,00 | 151 / +0,05 | 55 / -0,05 | 6 |
| SMA | long | cross | d200 | trail | 289 / +0,22 | 150 / +0,04 | 55 / +0,07 | 6 |
| SMA | long | cross | d50 | opp | 325 / +1,65 | 122 / +1,04 | 76 / +0,53 | 6 |
| SMA | long | cross | d50 | opp_stop | 325 / +1,47 | 122 / +1,19 | 76 / +0,81 | 6 |
| SMA | long | cross | d50 | target | 320 / -0,04 | 122 / +0,11 | 76 / +0,05 | 6 |
| SMA | long | cross | d50 | trail | 320 / +0,38 | 122 / +0,10 | 76 / +0,71 | 6 |
| SMA | long | cross | none | opp | 719 / +1,29 | 253 / +0,46 | 206 / +0,20 | 13 |
| SMA | long | cross | none | opp_stop | 719 / +1,01 | 253 / +0,60 | 206 / +0,31 | 13 |
| SMA | long | cross | none | target | 700 / -0,02 | 250 / +0,11 | 202 / +0,16 | 13 |
| SMA | long | cross | none | trail | 690 / +0,28 | 248 / -0,00 | 200 / +0,37 | 13 |
| SMA | long | pullback | d200 | opp | 242 / +1,43 | 112 / +0,12 | 55 / -0,15 | 5 |
| SMA | long | pullback | d200 | opp_stop | 314 / +1,36 | 154 / +0,14 | 71 / -0,03 | 6 |
| SMA | long | pullback | d200 | target | 392 / -0,07 | 176 / -0,12 | 83 / -0,18 | 7 |
| SMA | long | pullback | d200 | trail | 410 / +0,04 | 180 / +0,10 | 90 / +0,18 | 8 |
| SMA | long | pullback | d50 | opp | 310 / +1,37 | 114 / -0,17 | 78 / -0,16 | 6 |
| SMA | long | pullback | d50 | opp_stop | 399 / +1,36 | 159 / -0,26 | 95 / +0,14 | 7 |
| SMA | long | pullback | d50 | target | 514 / +0,00 | 171 / -0,24 | 114 / -0,20 | 9 |
| SMA | long | pullback | d50 | trail | 534 / +0,17 | 175 / -0,05 | 123 / -0,00 | 9 |
| SMA | long | pullback | none | opp | 486 / +1,22 | 176 / +0,05 | 135 / -0,03 | 9 |
| SMA | long | pullback | none | opp_stop | 624 / +1,24 | 244 / -0,11 | 190 / +0,08 | 12 |
| SMA | long | pullback | none | target | 786 / +0,00 | 269 / -0,12 | 227 / -0,03 | 15 |
| SMA | long | pullback | none | trail | 804 / +0,24 | 274 / +0,03 | 243 / +0,12 | 15 |
| EMA | short | confirm | d200 | opp | 259 / +0,16 | 106 / -0,39 | 126 / +0,46 | 6 |
| EMA | short | confirm | d200 | opp_stop | 375 / +0,14 | 168 / -0,48 | 187 / +0,28 | 8 |
| EMA | short | confirm | d200 | target | 578 / -0,04 | 230 / -0,11 | 296 / +0,03 | 13 |
| EMA | short | confirm | d200 | trail | 626 / -0,00 | 236 / -0,20 | 305 / +0,14 | 13 |
| EMA | short | confirm | d50 | opp | 321 / +0,08 | 153 / -0,39 | 130 / +0,52 | 7 |
| EMA | short | confirm | d50 | opp_stop | 470 / +0,08 | 219 / -0,28 | 193 / +0,32 | 10 |
| EMA | short | confirm | d50 | target | 712 / -0,09 | 326 / -0,07 | 301 / +0,01 | 15 |
| EMA | short | confirm | d50 | trail | 759 / -0,02 | 333 / -0,10 | 308 / +0,13 | 16 |
| EMA | short | confirm | none | opp | 491 / -0,04 | 200 / -0,26 | 170 / +0,35 | 10 |
| EMA | short | confirm | none | opp_stop | 714 / +0,04 | 297 / -0,23 | 252 / +0,28 | 14 |
| EMA | short | confirm | none | target | 1100 / -0,04 | 439 / -0,01 | 398 / +0,07 | 22 |
| EMA | short | confirm | none | trail | 1161 / -0,01 | 458 / -0,05 | 409 / +0,13 | 23 |
| EMA | short | cross | d200 | opp | 200 / +0,06 | 80 / -0,62 | 113 / +0,38 | 4 |
| EMA | short | cross | d200 | opp_stop | 200 / +0,24 | 80 / -0,60 | 113 / +0,28 | 4 |
| EMA | short | cross | d200 | target | 195 / +0,02 | 75 / +0,07 | 108 / +0,01 | 4 |
| EMA | short | cross | d200 | trail | 196 / -0,00 | 75 / -0,21 | 108 / -0,28 | 4 |
| EMA | short | cross | d50 | opp | 207 / -0,18 | 106 / -0,58 | 92 / +0,07 | 5 |
| EMA | short | cross | d50 | opp_stop | 207 / +0,07 | 106 / -0,49 | 92 / -0,01 | 5 |
| EMA | short | cross | d50 | target | 203 / -0,03 | 102 / +0,03 | 88 / +0,01 | 4 |
| EMA | short | cross | d50 | trail | 203 / -0,06 | 102 / -0,20 | 88 / -0,20 | 4 |
| EMA | short | cross | none | opp | 476 / -0,07 | 196 / -0,25 | 168 / +0,37 | 10 |
| EMA | short | cross | none | opp_stop | 476 / +0,08 | 196 / -0,28 | 168 / +0,38 | 10 |
| EMA | short | cross | none | target | 466 / +0,06 | 188 / +0,06 | 161 / +0,11 | 9 |
| EMA | short | cross | none | trail | 467 / -0,04 | 189 / -0,16 | 161 / -0,12 | 9 |
| EMA | short | pullback | d200 | opp | 207 / +0,15 | 80 / -0,18 | 90 / +0,84 | 4 |
| EMA | short | pullback | d200 | opp_stop | 286 / +0,17 | 120 / -0,40 | 133 / +0,57 | 6 |
| EMA | short | pullback | d200 | target | 455 / -0,05 | 176 / -0,19 | 230 / +0,01 | 10 |
| EMA | short | pullback | d200 | trail | 488 / -0,01 | 178 / -0,19 | 223 / +0,29 | 10 |
| EMA | short | pullback | d50 | opp | 264 / +0,18 | 119 / -0,22 | 99 / +0,74 | 5 |
| EMA | short | pullback | d50 | opp_stop | 370 / +0,17 | 168 / -0,18 | 147 / +0,45 | 8 |
| EMA | short | pullback | d50 | target | 581 / -0,06 | 254 / -0,11 | 242 / -0,02 | 12 |
| EMA | short | pullback | d50 | trail | 610 / +0,03 | 257 / -0,06 | 238 / +0,24 | 13 |
| EMA | short | pullback | none | opp | 367 / -0,02 | 147 / -0,15 | 122 / +0,50 | 7 |
| EMA | short | pullback | none | opp_stop | 502 / +0,10 | 205 / -0,08 | 175 / +0,46 | 10 |
| EMA | short | pullback | none | target | 788 / -0,06 | 313 / -0,04 | 290 / +0,01 | 16 |
| EMA | short | pullback | none | trail | 818 / +0,03 | 316 / +0,00 | 283 / +0,22 | 16 |
| SMA | short | confirm | d200 | opp | 343 / +0,02 | 112 / -0,53 | 147 / +0,50 | 7 |
| SMA | short | confirm | d200 | opp_stop | 504 / +0,03 | 176 / -0,36 | 235 / +0,24 | 10 |
| SMA | short | confirm | d200 | target | 578 / -0,10 | 210 / -0,11 | 296 / +0,07 | 12 |
| SMA | short | confirm | d200 | trail | 575 / -0,04 | 204 / -0,18 | 277 / +0,19 | 12 |
| SMA | short | confirm | d50 | opp | 415 / -0,01 | 166 / -0,48 | 140 / +0,82 | 8 |
| SMA | short | confirm | d50 | opp_stop | 608 / +0,05 | 249 / -0,29 | 222 / +0,37 | 12 |
| SMA | short | confirm | d50 | target | 712 / -0,09 | 289 / -0,06 | 292 / +0,04 | 15 |
| SMA | short | confirm | d50 | trail | 702 / -0,03 | 280 / -0,10 | 275 / +0,19 | 14 |
| SMA | short | confirm | none | opp | 665 / -0,21 | 234 / -0,41 | 202 / +0,40 | 13 |
| SMA | short | confirm | none | opp_stop | 987 / -0,10 | 358 / -0,19 | 314 / +0,20 | 19 |
| SMA | short | confirm | none | target | 1137 / -0,11 | 431 / -0,00 | 405 / +0,08 | 22 |
| SMA | short | confirm | none | trail | 1121 / -0,07 | 420 / -0,05 | 388 / +0,15 | 22 |
| SMA | short | cross | d200 | opp | 323 / +0,06 | 102 / -0,63 | 146 / +0,50 | 6 |
| SMA | short | cross | d200 | opp_stop | 323 / +0,12 | 102 / -0,48 | 146 / +0,27 | 6 |
| SMA | short | cross | d200 | target | 315 / -0,09 | 102 / -0,11 | 138 / +0,20 | 6 |
| SMA | short | cross | d200 | trail | 313 / +0,00 | 102 / -0,27 | 141 / -0,04 | 6 |
| SMA | short | cross | d50 | opp | 382 / -0,03 | 136 / -0,61 | 123 / +0,68 | 7 |
| SMA | short | cross | d50 | opp_stop | 382 / +0,07 | 136 / -0,46 | 123 / +0,39 | 7 |
| SMA | short | cross | d50 | target | 375 / -0,06 | 136 / -0,00 | 118 / +0,27 | 7 |
| SMA | short | cross | d50 | trail | 371 / -0,04 | 136 / -0,25 | 120 / +0,11 | 7 |
| SMA | short | cross | none | opp | 721 / -0,24 | 250 / -0,39 | 213 / +0,42 | 13 |
| SMA | short | cross | none | opp_stop | 721 / -0,09 | 250 / -0,23 | 213 / +0,28 | 13 |
| SMA | short | cross | none | target | 705 / -0,09 | 246 / -0,00 | 204 / +0,20 | 13 |
| SMA | short | cross | none | trail | 696 / -0,10 | 247 / -0,14 | 206 / +0,05 | 13 |
| SMA | short | pullback | d200 | opp | 273 / -0,04 | 94 / -0,31 | 128 / +0,52 | 6 |
| SMA | short | pullback | d200 | opp_stop | 367 / -0,05 | 129 / -0,29 | 178 / +0,42 | 8 |
| SMA | short | pullback | d200 | target | 424 / -0,12 | 159 / -0,09 | 233 / -0,01 | 9 |
| SMA | short | pullback | d200 | trail | 429 / -0,05 | 153 / -0,13 | 221 / +0,23 | 9 |
| SMA | short | pullback | d50 | opp | 336 / -0,22 | 137 / -0,28 | 126 / +0,65 | 7 |
| SMA | short | pullback | d50 | opp_stop | 446 / -0,08 | 179 / -0,22 | 177 / +0,39 | 9 |
| SMA | short | pullback | d50 | target | 510 / -0,13 | 210 / -0,08 | 232 / -0,06 | 11 |
| SMA | short | pullback | d50 | trail | 513 / -0,05 | 199 / -0,02 | 223 / +0,16 | 11 |
| SMA | short | pullback | none | opp | 514 / -0,27 | 197 / -0,25 | 171 / +0,34 | 10 |
| SMA | short | pullback | none | opp_stop | 672 / -0,10 | 250 / -0,05 | 237 / +0,31 | 13 |
| SMA | short | pullback | none | target | 787 / -0,09 | 306 / +0,00 | 308 / +0,03 | 16 |
| SMA | short | pullback | none | trail | 774 / -0,03 | 290 / +0,03 | 298 / +0,19 | 15 |

Short MA 30 × 60 na 4H: 72 variant, kladné OOS 6, kladné HOLDOUT 64, kladné ve všech třech obdobích 3.

## 5. Pro srovnání: nejlepší podle OOS (vybráno zpětně = ukázka přeučení, NE výběr)

| Směr | Kombinace | IS Ø R | OOS n / Ø R | HOLDOUT n / Ø R |
|---|---|---|---|---|
| long | 4h EMA 50/150 · cross · d50 · opp_stop | +7,52 | 66 / +4,46 | 45 / +0,27 |
| long | 4h EMA 40/150 · cross · d50 · opp_stop | +7,56 | 66 / +4,33 | 40 / +0,21 |
| long | 4h SMA 20/200 · cross · d50 · opp_stop | +7,25 | 71 / +4,23 | 42 / +0,84 |
| long | 4h EMA 40/200 · cross · none · opp_stop | +2,06 | 81 / +4,21 | 64 / +0,97 |
| long | 4h EMA 30/150 · cross · d50 · opp_stop | +6,77 | 75 / +4,05 | 44 / +0,33 |
| short | 2h EMA 10/200 · cross · d50 · trail | -0,04 | 129 / +0,65 | 167 / -0,38 |
| short | 2h EMA 10/200 · cross · d200 · trail | +0,06 | 107 / +0,49 | 199 / -0,38 |
| short | 2h EMA 5/200 · cross · d50 · trail | -0,05 | 158 / +0,46 | 216 / -0,24 |
| short | 6h EMA 50/60 · pullback · none · opp | -0,19 | 67 / +0,43 | 63 / +0,46 |
| short | 6h SMA 50/60 · pullback · none · opp_stop | +0,15 | 147 / +0,42 | 157 / +0,02 |

Z těchto zpětně nejlepších zůstalo kladných v HOLDOUT 7 z 10.

## Závěr

❌ **Žádná kombinace nesplnila předem stanovená kritéria.** Skener se nemění.

Celá tabulka všech kombinací včetně jejich náhodných srovnání: `reports/ma_grid_all.csv.gz`.

Nejde o finanční poradenství.