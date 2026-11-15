# 🧩 Studie kombinací ukazatelů, signálů a spouštěčů

Průběžná studie: spouštěč z atlasu + 1–2 potvrzení/filtry z jiných rodin nebo kontextu. Metoda, filtry a pravidla jsou stanoveny předem v hlavičce `research/experiments/combo_study.py`; data, náklady (MEXC 0,05 %/stranu), simulace a dělení IS (do 12/2023) / OOS (1/2024–6/2025) / HOLDOUT (7/2025–) jsou stejné jako v atlasu. Papírově, nic nejde na skutečné peníze. Nejde o finanční poradenství.

- Hotových dílů: **8**, testovaných kombinací celkem (vč. samotných spouštěčů): **1632** – při tolika testech projde pravidlem i něco čistě náhodou, proto jen papír.
- Poslední díl 8: **pair 6H** (skupiny volatilita, momentum, sentiment), 252 kombinací + 12 spouštěčů samotných, 3 s; základní pravidlo splnilo 1, prošlo vč. citlivosti a režimů 1.
- Mřížka (stanovena před výpočtem): spouštěče macd 12/26/9/signal · opp · long; price_ma sma/20 · opp · long; ma_cross ema/10/30/cross · opp · long; boll_break 50/2.0 · opp · long; rsi_mom 50 · opp · long; keltner 1.5 · opp · long; ma_cross ema/20/60/cross · target · short; macd 19/39/9/signal · opp_stop · short; vol_break 20/2.5 · target · short; donchian 55 · opp_stop · short; price_ma sma/100 · opp · short; roc 100 · opp · short × filtry atrlo:0.3, atrlo:0.5, atrlo:0.7, atrhi:0.3, atrhi:0.5, atrhi:0.7, rsi:45, rsi:50, rsi:55, rsi:60, rsix:60, rsix:70, rsix:80, macd:sig, macd:zero, fng:30, fng:45, fng:60, fngg:40, fngg:55, fngg:70.
- Další díl: **pair 12H** (skupiny trend, režim, objem).

## Změny v registru v tomto běhu

- 🆕 Kombinace: MACD 19 39 9 signal + RSI ≥ 50 · 6H short → papír (combo_study: díl 8, OOS +0.17 R (t +2.2), HOLDOUT +0.16 R (t +1.9), spouštěč sám OOS +0.10 R); režimy: býčí, medvědí, boční; nahradila Kombinace: Průraz s objemem 20 2.5 + F&G ≤ 60 · 4H short

## Combo strategie v registru (10 aktivních, limit 10)

| Strategie | Stav | OOS Ø R (t) | HOLDOUT Ø R (t) | Spouštěč sám OOS | Režimy | Papír |
|---|---|---|---|---|---|---|
| Kombinace: Bollinger průraz 20 2.5 + trend EMA100 · 1H long | papír | +0,18 (+2,6) | +0,33 (+2,3) | +0,11 | býčí, medvědí, boční | 0 obch., Ø – R |
| Kombinace: Průraz s objemem 55 2.5 + režim side · 1H short | papír | +0,23 (+2,1) | +0,23 (+2,2) | +0,09 | boční | 0 obch., Ø – R |
| Kombinace: Bollinger průraz 20 2.5 + ATR pctl ≥ 0,3 · 1H long | papír | +0,22 (+3,4) | +0,32 (+2,8) | +0,11 | býčí, medvědí, boční, panika | 1 obch., Ø -0,69 R |
| Kombinace: Bollinger průraz 20 2.5 + ATR pctl ≥ 0,7 · 1H long | papír | +0,26 (+2,7) | +0,38 (+2,7) | +0,11 | býčí, medvědí, boční, panika | 0 obch., Ø – R |
| Kombinace: Bollinger průraz 50 2.5 + trend EMA200 · 2H long | papír | +0,58 (+2,2) | +0,75 (+2,3) | +0,46 | býčí, medvědí, boční, panika | 0 obch., Ø – R |
| Kombinace: Bollinger průraz 50 2.5 + denní 50 · 2H long | papír | +0,60 (+2,2) | +1,25 (+2,8) | +0,46 | býčí, boční, panika | 0 obch., Ø – R |
| Kombinace: Bollinger průraz 50 2.5 + F&G ≥ 40 · 2H long | papír | +0,52 (+2,2) | +1,47 (+3,3) | +0,46 | býčí, medvědí, boční, panika | 0 obch., Ø – R |
| Kombinace: Bollinger průraz 50 2.5 + ATR pctl ≥ 0,3 · 2H long | papír | +0,68 (+2,5) | +0,42 (+1,7) | +0,46 | býčí, medvědí, boční, panika | 0 obch., Ø – R |
| Kombinace: Bollinger průraz 50 2.5 + režim notpanic · 4H short | papír | +0,33 (+3,3) | +0,24 (+2,7) | +0,20 | býčí, medvědí, boční | 0 obch., Ø – R |
| Kombinace: MACD 19 39 9 signal + RSI ≥ 50 · 6H short | papír | +0,17 (+2,2) | +0,16 (+1,9) | +0,10 | býčí, medvědí, boční | 0 obch., Ø – R |

## Top 10 kombinací (podle min(OOS t, HOLDOUT t), všechny díly)

| Díl | TF | Kombinace | Výstup · směr | IS Ø R (t) | OOS Ø R (t) | HOLDOUT Ø R (t) | p95 náhody OOS / HOLD | Spouštěč sám OOS | Obchodů IS/OOS/HOLD | Výsledek |
|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 1H | Bollinger průraz 20 2.5 + ATR pctl ≥ 0,3 | opp · long | +0,19 (+4,3) | +0,22 (+3,4) | +0,32 (+2,8) | +0,04 / +0,04 | +0,11 | 2462/773/779 | ✅ prošlo |
| 5 | 4H | Bollinger průraz 50 2.5 + režim notpanic | target · short | +0,14 (+2,5) | +0,33 (+3,3) | +0,24 (+2,7) | +0,14 / +0,16 | +0,20 | 452/154/188 | ✅ prošlo |
| 2 | 1H | Bollinger průraz 20 2.5 + ATR pctl ≥ 0,7 | opp · long | +0,24 (+3,9) | +0,26 (+2,7) | +0,38 (+2,7) | +0,13 / +0,05 | +0,11 | 1116/349/393 | ✅ prošlo |
| 2 | 1H | Bollinger průraz 20 2.5 + ATR pctl ≥ 0,5 | opp · long | +0,27 (+5,0) | +0,29 (+3,7) | +0,29 (+2,6) | +0,09 / +0,04 | +0,11 | 1738/533/588 | ✅ prošlo |
| 5 | 4H | Bollinger průraz 50 2.5 + trend EMA50 | target · short | +0,11 (+2,1) | +0,23 (+2,6) | +0,25 (+2,8) | +0,10 / +0,21 | +0,20 | 535/192/189 | ❌ neporáží spouštěč o 0,05 R |
| 2 | 1H | Bollinger průraz 20 2.5 + MACD zero | opp · long | +0,23 (+5,5) | +0,15 (+2,5) | +0,25 (+2,5) | +0,08 / +0,05 | +0,11 | 3130/1018/926 | ❌ neporáží spouštěč o 0,05 R |
| 6 | 4H | Průraz s objemem 20 2.5 + F&G ≤ 30 | target · short | +0,31 (+2,5) | +0,29 (+2,5) | +0,53 (+2,4) | +0,25 / +0,19 | +0,19 | 90/110/32 | ❌ málo obchodů |
| 5 | 4H | Bollinger průraz 50 2.5 + trend EMA100 | target · short | +0,10 (+1,8) | +0,24 (+2,6) | +0,23 (+2,4) | +0,06 / +0,16 | +0,20 | 473/181/177 | ❌ neporáží spouštěč o 0,05 R |
| 8 | 6H | Cena × průměr sma 20 + ATR pctl ≤ 0,3 | opp · long | +0,31 (+4,5) | +0,20 (+2,5) | +0,28 (+2,4) | +0,15 / +0,31 | +0,15 | 1174/412/426 | ❌ pod p95 náhody, neporáží spouštěč o 0,05 R |
| 6 | 4H | Bollinger průraz 50 2.5 + F&G ≥ 70 | target · short | +0,14 (+1,7) | +0,74 (+2,6) | +0,28 (+2,3) | +0,04 / +0,14 | +0,20 | 207/16/103 | ❌ málo obchodů |

## Co filtry dělají se spouštěči (páry, průměr přes spouštěče)

| TF | Filtr | Spouštěčů | Ø zlepšení IS | Ø zlepšení OOS | Podíl OOS zlepšení > 0 | Splnilo základní pravidlo |
|---|---|---|---|---|---|---|
| 1H | atrhi:0.3 | 9 | +0,00 | +0,02 | 67% | 1 |
| 1H | atrhi:0.5 | 9 | +0,04 | +0,03 | 58% | 1 |
| 1H | atrhi:0.7 | 9 | +0,05 | +0,12 | 67% | 2 |
| 1H | atrlo:0.3 | 9 | +0,05 | -0,06 | 42% | 0 |
| 1H | atrlo:0.5 | 9 | +0,00 | -0,05 | 33% | 0 |
| 1H | atrlo:0.7 | 9 | +0,02 | -0,05 | 42% | 0 |
| 1H | d:200 | 9 | +0,09 | -0,03 | 42% | 0 |
| 1H | d:50 | 9 | +0,18 | -0,04 | 25% | 0 |
| 1H | ema:100 | 9 | +0,08 | -0,00 | 42% | 1 |
| 1H | ema:200 | 9 | +0,10 | +0,02 | 42% | 2 |
| 1H | ema:50 | 9 | -0,01 | -0,01 | 33% | 1 |
| 1H | fng:30 | 9 | -0,27 | -0,07 | 42% | 0 |
| 1H | fng:45 | 9 | -0,17 | +0,04 | 83% | 0 |
| 1H | fng:60 | 9 | -0,13 | -0,06 | 58% | 0 |
| 1H | fngg:40 | 9 | +0,11 | -0,04 | 25% | 0 |
| 1H | fngg:55 | 9 | +0,26 | -0,11 | 33% | 0 |
| 1H | fngg:70 | 9 | +0,48 | -0,08 | 8% | 0 |
| 1H | macd:sig | 9 | -0,01 | -0,01 | 33% | 0 |
| 1H | macd:zero | 9 | -0,01 | +0,01 | 67% | 0 |
| 1H | reg:notpanic | 9 | -0,00 | +0,14 | 100% | 4 |
| 1H | reg:side | 9 | -0,06 | +0,04 | 58% | 1 |
| 1H | reg:trend | 9 | +0,17 | +0,15 | 83% | 0 |
| 1H | rsi:45 | 9 | -0,00 | -0,00 | 0% | 0 |
| 1H | rsi:50 | 9 | +0,00 | +0,00 | 42% | 0 |
| 1H | rsi:55 | 9 | -0,01 | -0,00 | 33% | 0 |
| 1H | rsi:60 | 9 | +0,03 | -0,03 | 25% | 0 |
| 1H | rsix:60 | 9 | -0,17 | +0,06 | 58% | 1 |
| 1H | rsix:70 | 9 | -0,02 | -0,04 | 42% | 0 |
| 1H | rsix:80 | 9 | -0,00 | +0,01 | 42% | 0 |
| 1H | vol:1 | 9 | +0,04 | -0,02 | 42% | 0 |
| 1H | vol:1.5 | 9 | +0,06 | -0,04 | 42% | 0 |
| 1H | vol:2 | 9 | +0,08 | -0,01 | 50% | 0 |
| 2H | atrhi:0.3 | 11 | +0,01 | +0,13 | 67% | 1 |
| 2H | atrhi:0.5 | 11 | -0,01 | +0,24 | 50% | 1 |
| 2H | atrhi:0.7 | 11 | +0,01 | +0,32 | 67% | 0 |
| 2H | atrlo:0.3 | 11 | +0,07 | -0,19 | 33% | 0 |
| 2H | atrlo:0.5 | 11 | +0,11 | -0,13 | 50% | 0 |
| 2H | atrlo:0.7 | 11 | +0,05 | -0,03 | 50% | 0 |
| 2H | d:200 | 11 | +0,10 | +0,03 | 42% | 1 |
| 2H | d:50 | 11 | +0,18 | -0,03 | 33% | 1 |
| 2H | ema:100 | 11 | +0,08 | -0,01 | 50% | 0 |
| 2H | ema:200 | 11 | +0,15 | +0,04 | 67% | 1 |
| 2H | ema:50 | 11 | +0,04 | +0,00 | 58% | 0 |
| 2H | fng:30 | 11 | -0,38 | -0,21 | 25% | 0 |
| 2H | fng:45 | 11 | -0,22 | -0,23 | 25% | 0 |
| 2H | fng:60 | 11 | -0,17 | -0,21 | 50% | 0 |
| 2H | fngg:40 | 11 | +0,16 | -0,03 | 42% | 1 |
| 2H | fngg:55 | 11 | +0,29 | -0,04 | 50% | 0 |
| 2H | fngg:70 | 11 | +0,64 | -0,01 | 50% | 0 |
| 2H | macd:sig | 11 | +0,01 | +0,05 | 83% | 0 |
| 2H | macd:zero | 11 | +0,01 | +0,02 | 58% | 0 |
| 2H | reg:notpanic | 11 | -0,04 | +0,18 | 100% | 3 |
| 2H | reg:side | 11 | -0,06 | +0,23 | 75% | 0 |
| 2H | reg:trend | 11 | +0,18 | +0,28 | 58% | 1 |
| 2H | rsi:45 | 11 | +0,00 | +0,00 | 8% | 0 |
| 2H | rsi:50 | 11 | +0,00 | +0,00 | 17% | 0 |
| 2H | rsi:55 | 11 | +0,02 | +0,03 | 58% | 1 |
| 2H | rsi:60 | 11 | +0,09 | +0,07 | 50% | 0 |
| 2H | rsix:60 | 11 | -0,49 | +0,25 | 33% | 0 |
| 2H | rsix:70 | 11 | -0,07 | -0,11 | 17% | 0 |
| 2H | rsix:80 | 11 | -0,02 | +0,01 | 50% | 0 |
| 2H | vol:1 | 11 | +0,05 | +0,04 | 50% | 0 |
| 2H | vol:1.5 | 11 | +0,11 | +0,05 | 50% | 0 |
| 2H | vol:2 | 11 | +0,15 | +0,05 | 67% | 0 |
| 4H | atrhi:0.3 | 11 | -0,05 | +0,09 | 42% | 0 |
| 4H | atrhi:0.5 | 11 | -0,06 | +0,14 | 50% | 0 |
| 4H | atrhi:0.7 | 11 | -0,06 | +0,38 | 42% | 0 |
| 4H | atrlo:0.3 | 11 | +0,06 | -0,08 | 50% | 0 |
| 4H | atrlo:0.5 | 11 | +0,05 | -0,08 | 50% | 0 |
| 4H | atrlo:0.7 | 11 | +0,04 | -0,09 | 58% | 0 |
| 4H | d:200 | 11 | +0,08 | -0,03 | 25% | 0 |
| 4H | d:50 | 11 | +0,09 | -0,07 | 25% | 0 |
| 4H | ema:100 | 11 | +0,09 | +0,05 | 50% | 0 |
| 4H | ema:200 | 11 | +0,12 | +0,03 | 42% | 1 |
| 4H | ema:50 | 11 | +0,09 | -0,01 | 50% | 0 |
| 4H | fng:30 | 11 | -0,27 | -0,17 | 42% | 1 |
| 4H | fng:45 | 11 | -0,18 | -0,22 | 50% | 0 |
| 4H | fng:60 | 11 | -0,11 | -0,12 | 42% | 1 |
| 4H | fngg:40 | 11 | +0,11 | -0,02 | 33% | 0 |
| 4H | fngg:55 | 11 | +0,17 | -0,10 | 58% | 0 |
| 4H | fngg:70 | 11 | +0,38 | +0,05 | 50% | 0 |
| 4H | macd:sig | 11 | +0,00 | +0,03 | 58% | 0 |
| 4H | macd:zero | 11 | +0,06 | +0,01 | 42% | 0 |
| 4H | reg:notpanic | 11 | -0,02 | +0,17 | 92% | 2 |
| 4H | reg:side | 11 | +0,04 | +0,15 | 75% | 0 |
| 4H | reg:trend | 11 | +0,09 | +0,10 | 58% | 0 |
| 4H | rsi:45 | 11 | +0,02 | +0,01 | 33% | 0 |
| 4H | rsi:50 | 11 | +0,03 | +0,04 | 50% | 0 |
| 4H | rsi:55 | 11 | +0,07 | +0,05 | 33% | 0 |
| 4H | rsi:60 | 11 | +0,12 | +0,13 | 58% | 0 |
| 4H | rsix:60 | 11 | -0,02 | -0,29 | 17% | 0 |
| 4H | rsix:70 | 11 | -0,05 | +0,07 | 75% | 0 |
| 4H | rsix:80 | 11 | +0,00 | +0,02 | 67% | 0 |
| 4H | vol:1 | 11 | +0,06 | +0,07 | 58% | 0 |
| 4H | vol:1.5 | 11 | +0,15 | +0,08 | 42% | 0 |
| 4H | vol:2 | 11 | +0,17 | +0,18 | 50% | 0 |
| 6H | atrhi:0.3 | 12 | -0,48 | +0,11 | 50% | 0 |
| 6H | atrhi:0.5 | 12 | -0,54 | +0,18 | 50% | 0 |
| 6H | atrhi:0.7 | 12 | -0,62 | +0,32 | 50% | 0 |
| 6H | atrlo:0.3 | 12 | +0,69 | -0,07 | 50% | 0 |
| 6H | atrlo:0.5 | 12 | +0,35 | -0,07 | 50% | 0 |
| 6H | atrlo:0.7 | 12 | +0,20 | -0,06 | 50% | 0 |
| 6H | d:200 | 12 | -0,12 | -0,08 | 25% | 0 |
| 6H | d:50 | 12 | +0,59 | -0,02 | 25% | 0 |
| 6H | ema:100 | 12 | +0,64 | +0,00 | 50% | 0 |
| 6H | ema:200 | 12 | +0,59 | -0,02 | 33% | 1 |
| 6H | ema:50 | 12 | -0,19 | +0,02 | 33% | 0 |
| 6H | fng:30 | 12 | -0,60 | -0,20 | 50% | 0 |
| 6H | fng:45 | 12 | -0,58 | -0,18 | 50% | 0 |
| 6H | fng:60 | 12 | -0,52 | -0,16 | 42% | 0 |
| 6H | fngg:40 | 12 | +0,27 | -0,01 | 42% | 0 |
| 6H | fngg:55 | 12 | +0,58 | -0,03 | 50% | 0 |
| 6H | fngg:70 | 12 | +1,36 | +0,09 | 67% | 0 |
| 6H | macd:sig | 12 | +0,15 | +0,00 | 42% | 0 |
| 6H | macd:zero | 12 | -0,20 | -0,00 | 25% | 0 |
| 6H | reg:notpanic | 12 | -0,29 | +0,14 | 83% | 1 |
| 6H | reg:side | 12 | -0,29 | -0,00 | 50% | 0 |
| 6H | reg:trend | 12 | -0,03 | +0,12 | 58% | 1 |
| 6H | rsi:45 | 12 | -0,30 | +0,01 | 25% | 0 |
| 6H | rsi:50 | 12 | -0,25 | +0,01 | 33% | 1 |
| 6H | rsi:55 | 12 | -0,14 | +0,05 | 42% | 0 |
| 6H | rsi:60 | 12 | -0,26 | +0,26 | 75% | 0 |
| 6H | rsix:60 | 12 | -0,15 | -0,23 | 25% | 0 |
| 6H | rsix:70 | 12 | -0,02 | +0,06 | 83% | 0 |
| 6H | rsix:80 | 12 | +0,00 | +0,01 | 67% | 0 |
| 6H | vol:1 | 12 | +0,50 | +0,13 | 75% | 0 |
| 6H | vol:1.5 | 12 | +1,22 | +0,20 | 92% | 1 |
| 6H | vol:2 | 12 | +2,34 | +0,29 | 75% | 0 |

## Proč neprošly (nejčastější důvody)

- pod p95 náhody: 1371×
- OOS t < 2: 1091×
- neporáží spouštěč o 0,05 R: 1072×
- HOLDOUT ≤ 0: 480×
- OOS ≤ 0: 232×
- IS ≤ 0: 110×
- málo obchodů: 100×
- reg: bez zlepšení v IS: 3×

## Plán studie

Páry spouštěč + 1 filtr (každý TF ve dvou skupinách filtrů) → nejlepší páry podle IS + druhý filtr → citlivost sousedních parametrů spouštěče. Pak znovu na čerstvých datech. Funding/OI zatím chybí historická data.

Povyšování a vyřazování combo strategií dělá laboratoř (`research/lab.py`) podle papírových výsledků.
