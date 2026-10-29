# 🧠 Kontextová brána – výsledky testu

Spuštěno 2026-10-29 20:06 UTC · 24 aktivních strategií × 8 mincí · 67507 signálů · F&G ano · 1233 s.
Pravidla stanovena předem (hlavička research/experiments/context_gate.py). IS < 2024-01-01 ≤ OOS < 2025-07-01 ≤ HOLDOUT.

## A) Brána pro současné strategie: **NEPROŠLA ❌**

Rozdíl ponechané − vyřazené v OOS+HOLDOUT: – R, t – (klastry po týdnech). Ø R ponechaných lepší než všech: OOS ne, HOLDOUT ne.

| období | všechny: n | Ø R | Σ R | výhry | brána: n | Ø R | Σ R | výhry | vyřazené Ø R |
|---|---|---|---|---|---|---|---|---|---|
| IS | 40022 | +0,468 | +18743 | 32% | 40022 | +0,468 | +18743 | 32% | – |
| OOS | 14333 | +0,406 | +5825 | 34% | 14333 | +0,406 | +5825 | 34% | – |
| HOLDOUT | 13152 | +0,326 | +4284 | 33% | 13152 | +0,326 | +4284 | 33% | – |
| posl. 180 dní | 5064 | +0,637 | +3225 | 33% | 5064 | +0,637 | +3225 | 33% | – |

Křivka (OOS+HOLDOUT): kolik vyřadit → Ø R ponechaných

| vyřadit spodních | ponecháno | Ø R | Σ R |
|---|---|---|---|
| 25% | 27485 | +0,368 | +10108 |
| 40% | 27485 | +0,368 | +10108 |
| 50% | 27485 | +0,368 | +10108 |
| 60% | 27485 | +0,368 | +10108 |
| 75% | 27485 | +0,368 | +10108 |

### Co kontext říká (IS třetiny → Ø R v OOS+HOLDOUT)

| metrika | váha | t (IS) | dolní třetina | střed | horní třetina |
|---|---|---|---|---|---|
| denní trend mince | +0 | +1,5 | +0,428 | – | +0,307 |
| denní trend BTC | +0 | +1,4 | +0,328 | – | +0,394 |
| trendovost (denní) | +0 | +0,5 | +0,602 | +0,285 | +0,143 |
| síla trendu ADX | +0 | -0,7 | +0,689 | +0,170 | +0,090 |
| boční pila (chop) | +0 | +0,3 | +0,182 | +0,261 | +0,647 |
| poloha v rozpětí 30 dní | +0 | +1,8 | +0,305 | +0,527 | +0,259 |
| trendovost na TF signálu | +0 | -0,1 | +0,350 | +0,387 | +0,367 |
| pokračování průrazů | +0 | -1,7 | +0,675 | +0,246 | +0,214 |
| uklidnění před signálem | +0 | -0,1 | +0,245 | +0,284 | +0,597 |
| zavření svíčky | +0 | +1,0 | +0,324 | +0,396 | +0,381 |
| objem průrazu | +0 | -0,1 | +0,226 | +0,402 | +0,454 |
| přetažení od EMA20 | +0 | -0,5 | +0,317 | +0,290 | +0,488 |
| nálada (strach/chamtivost) | +0 | +1,5 | +0,372 | +0,188 | +0,463 |
| změna nálady | +0 | -0,0 | +0,328 | +0,873 | +0,149 |

### Trendový vs. boční kontext (současné strategie, Ø R)

| období | trendový: n | Ø R | boční: n | Ø R |
|---|---|---|---|---|
| IS | 29555 | +0,461 | 10467 | +0,490 |
| OOS | 11094 | +0,333 | 3239 | +0,657 |
| HOLDOUT | 9282 | +0,151 | 3870 | +0,744 |
| posl. 180 dní | 3644 | +0,232 | 1420 | +1,677 |

### Po strategiích (OOS+HOLDOUT)

| strategie | n | Ø R všech | Ø R s bránou | podíl ponechaných |
|---|---|---|---|---|
| Bollinger průraz 20 2.5 · 4H long | 779 | +0,510 | +0,510 | 100% |
| Bollinger průraz 20 2.5 · 6H long | 523 | +0,691 | +0,691 | 100% |
| Bollinger průraz 50 2.5 · 4H short | 415 | +0,292 | +0,292 | 100% |
| Donchian průraz 100 · 1H long | 2313 | +0,291 | +0,291 | 100% |
| Donchian průraz 20 · 6H long | 678 | +0,919 | +0,919 | 100% |
| Keltner průraz 2.5 · 2H short | 875 | +0,246 | +0,246 | 100% |
| Keltner průraz 2.5 · 4H short | 425 | +0,280 | +0,280 | 100% |
| Keltner průraz 2.5 · 6H long | 296 | +0,692 | +0,692 | 100% |
| Protnutí průměrů ema 5 50 pullback · 1H long | 6041 | +0,449 | +0,449 | 100% |
| Protnutí průměrů ema 50 60 cross · 6H long | 168 | +0,366 | +0,366 | 100% |
| Protnutí průměrů sma 20 50 cross · 2H short | 605 | +0,156 | +0,156 | 100% |
| Protnutí průměrů sma 30 60 cross · 4H long | 374 | +0,289 | +0,289 | 100% |
| MACD 19 39 9 signal · 12H long | 444 | +0,432 | +0,432 | 100% |
| MACD 19 39 9 signal · 2H long | 2304 | +0,196 | +0,196 | 100% |
| Cena × průměr ema 200 · 4H long | 892 | +0,525 | +0,525 | 100% |
| RSI momentum 60 · 2H long | 3191 | +0,189 | +0,189 | 100% |
| RSI momentum 60 · 4H long | 1531 | +0,380 | +0,380 | 100% |
| RSI momentum 60 · 6H long | 982 | +0,405 | +0,405 | 100% |
| Supertrend 10 3.0 · 4H short | 238 | +0,411 | +0,411 | 100% |
| Supertrend 10 3.0 · 6H short | 244 | +0,341 | +0,341 | 100% |
| Průraz s objemem 20 1.5 · 6H long | 434 | +1,403 | +1,403 | 100% |
| Průraz s objemem 20 2.5 · 12H long | 103 | +0,422 | +0,422 | 100% |
| Průraz s objemem 55 1.5 · 1H long | 2166 | +0,255 | +0,255 | 100% |
| Průraz s objemem 55 2.5 · 1H long | 1464 | +0,231 | +0,231 | 100% |

Brána zlepšila Ø R u 0 z 24 strategií.

## B) Návrat do rozpětí jen v bočním kontextu

Boční kontext = pokračování průrazů < 0.33 a denní trendovost < 0.22 (mediány IS).
Prošlo pravidlem: bez kontextu 2, v bočním kontextu **1**, v trendovém 3 (z 360 kombinací).

| kandidát | IS Ø R | OOS Ø R (t) | HOLDOUT Ø R (t) | n IS/OOS/HOLD |
|---|---|---|---|---|
| Sweep & reclaim 55 · 4H long | +0,031 | +0,377 (+2,3) | +0,005 (+0,0) | 403/134/184 |

Poznámky: každý signál simulovaný samostatně (bez pravidla „jedna pozice naráz“); funding futures není započten; mnoho testovaných kombinací v části B znamená, že část průchodů může být náhoda – proto jen papír.
Papírově, nejde o finanční poradenství.
