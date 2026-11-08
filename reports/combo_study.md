# 🧩 Studie kombinací ukazatelů, signálů a spouštěčů

Průběžná studie: spouštěč z atlasu + 1–2 potvrzení/filtry z jiných rodin nebo kontextu. Metoda, filtry a pravidla jsou stanoveny předem v hlavičce `research/experiments/combo_study.py`; data, náklady (MEXC 0,05 %/stranu), simulace a dělení IS (do 12/2023) / OOS (1/2024–6/2025) / HOLDOUT (7/2025–) jsou stejné jako v atlasu. Papírově, nic nejde na skutečné peníze. Nejde o finanční poradenství.

- Hotových dílů: **4**, testovaných kombinací celkem (vč. samotných spouštěčů): **816** – při tolika testech projde pravidlem i něco čistě náhodou, proto jen papír.
- Poslední díl 4: **pair 2H** (skupiny volatilita, momentum, sentiment), 252 kombinací + 12 spouštěčů samotných, 2 s; základní pravidlo splnilo 4, prošlo vč. citlivosti a režimů 3.
- Mřížka (stanovena před výpočtem): spouštěče ma_cross sma/20/200/confirm · opp · long; macd 12/26/9/zero · opp · long; donchian 55 · opp · long; price_ma ema/200 · opp · long; vol_break 55/1.5 · opp · long; boll_break 50/2.5 · opp · long; ma_cross ema/30/200/cross · target · short; boll_break 20/2.5 · target · short; vol_break 55/2.5 · target · short; price_ma sma/50 · target · short; macd 5/35/5/zero · opp_stop · short; donchian 55 · target · short × filtry atrlo:0.3, atrlo:0.5, atrlo:0.7, atrhi:0.3, atrhi:0.5, atrhi:0.7, rsi:45, rsi:50, rsi:55, rsi:60, rsix:60, rsix:70, rsix:80, macd:sig, macd:zero, fng:30, fng:45, fng:60, fngg:40, fngg:55, fngg:70.
- Další díl: **pair 4H** (skupiny trend, režim, objem).

## Změny v registru v tomto běhu

- 🆕 Kombinace: Bollinger průraz 50 2.5 + F&G ≥ 40 · 2H long → papír (combo_study: díl 4, OOS +0.52 R (t +2.2), HOLDOUT +1.47 R (t +3.3), spouštěč sám OOS +0.46 R); režimy: býčí, medvědí, boční, panika
- 🆕 Kombinace: Bollinger průraz 50 2.5 + ATR pctl ≥ 0,3 · 2H long → papír (combo_study: díl 4, OOS +0.68 R (t +2.5), HOLDOUT +0.42 R (t +1.7), spouštěč sám OOS +0.46 R); režimy: býčí, medvědí, boční, panika

## Combo strategie v registru (8 aktivních, limit 10)

| Strategie | Stav | OOS Ø R (t) | HOLDOUT Ø R (t) | Spouštěč sám OOS | Režimy | Papír |
|---|---|---|---|---|---|---|
| Kombinace: Bollinger průraz 20 2.5 + trend EMA100 · 1H long | papír | +0,18 (+2,6) | +0,33 (+2,3) | +0,11 | býčí, medvědí, boční | 0 obch., Ø – R |
| Kombinace: Průraz s objemem 55 2.5 + režim side · 1H short | papír | +0,23 (+2,1) | +0,23 (+2,2) | +0,09 | boční | 0 obch., Ø – R |
| Kombinace: Bollinger průraz 20 2.5 + ATR pctl ≥ 0,3 · 1H long | papír | +0,22 (+3,4) | +0,32 (+2,8) | +0,11 | býčí, medvědí, boční, panika | 0 obch., Ø – R |
| Kombinace: Bollinger průraz 20 2.5 + ATR pctl ≥ 0,7 · 1H long | papír | +0,26 (+2,7) | +0,38 (+2,7) | +0,11 | býčí, medvědí, boční, panika | 0 obch., Ø – R |
| Kombinace: Bollinger průraz 50 2.5 + trend EMA200 · 2H long | papír | +0,58 (+2,2) | +0,75 (+2,3) | +0,46 | býčí, medvědí, boční, panika | 0 obch., Ø – R |
| Kombinace: Bollinger průraz 50 2.5 + denní 50 · 2H long | papír | +0,60 (+2,2) | +1,25 (+2,8) | +0,46 | býčí, boční, panika | 0 obch., Ø – R |
| Kombinace: Bollinger průraz 50 2.5 + F&G ≥ 40 · 2H long | papír | +0,52 (+2,2) | +1,47 (+3,3) | +0,46 | býčí, medvědí, boční, panika | 0 obch., Ø – R |
| Kombinace: Bollinger průraz 50 2.5 + ATR pctl ≥ 0,3 · 2H long | papír | +0,68 (+2,5) | +0,42 (+1,7) | +0,46 | býčí, medvědí, boční, panika | 0 obch., Ø – R |

## Top 10 kombinací (podle min(OOS t, HOLDOUT t), všechny díly)

| Díl | TF | Kombinace | Výstup · směr | IS Ø R (t) | OOS Ø R (t) | HOLDOUT Ø R (t) | p95 náhody OOS / HOLD | Spouštěč sám OOS | Obchodů IS/OOS/HOLD | Výsledek |
|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 1H | Bollinger průraz 20 2.5 + ATR pctl ≥ 0,3 | opp · long | +0,19 (+4,3) | +0,22 (+3,4) | +0,32 (+2,8) | +0,04 / +0,04 | +0,11 | 2462/773/779 | ✅ prošlo |
| 2 | 1H | Bollinger průraz 20 2.5 + ATR pctl ≥ 0,7 | opp · long | +0,24 (+3,9) | +0,26 (+2,7) | +0,38 (+2,7) | +0,13 / +0,05 | +0,11 | 1116/349/393 | ✅ prošlo |
| 2 | 1H | Bollinger průraz 20 2.5 + ATR pctl ≥ 0,5 | opp · long | +0,27 (+5,0) | +0,29 (+3,7) | +0,29 (+2,6) | +0,09 / +0,04 | +0,11 | 1738/533/588 | ✅ prošlo |
| 2 | 1H | Bollinger průraz 20 2.5 + MACD zero | opp · long | +0,23 (+5,5) | +0,15 (+2,5) | +0,25 (+2,5) | +0,08 / +0,05 | +0,11 | 3130/1018/926 | ❌ neporáží spouštěč o 0,05 R |
| 2 | 1H | Bollinger průraz 20 2.5 + RSI ≥ 60 | opp · long | +0,21 (+5,4) | +0,15 (+2,7) | +0,21 (+2,3) | +0,13 / +0,11 | +0,11 | 3419/1069/1031 | ❌ neporáží spouštěč o 0,05 R |
| 1 | 1H | Bollinger průraz 20 2.5 + trend EMA100 | opp · long | +0,28 (+5,7) | +0,18 (+2,6) | +0,33 (+2,3) | +0,10 / +0,14 | +0,11 | 2334/761/629 | ✅ prošlo |
| 3 | 2H | Bollinger průraz 50 2.5 + trend EMA200 | opp · long | +1,33 (+6,0) | +0,58 (+2,2) | +0,75 (+2,3) | +0,30 / +0,50 | +0,46 | 697/239/187 | ✅ prošlo |
| 3 | 2H | Bollinger průraz 50 2.5 + denní 50 | opp · long | +1,31 (+5,4) | +0,60 (+2,2) | +1,25 (+2,8) | +0,42 / +0,65 | +0,46 | 567/200/130 | ✅ prošlo |
| 1 | 1H | Bollinger průraz 20 2.5 + objem×2 | opp · long | +0,25 (+5,2) | +0,14 (+2,2) | +0,27 (+2,5) | +0,02 / +0,08 | +0,11 | 2418/816/803 | ❌ neporáží spouštěč o 0,05 R |
| 4 | 2H | Bollinger průraz 50 2.5 + F&G ≥ 40 | opp · long | +1,10 (+5,1) | +0,52 (+2,2) | +1,47 (+3,3) | +0,28 / +0,65 | +0,46 | 656/277/129 | ✅ prošlo |

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

## Proč neprošly (nejčastější důvody)

- pod p95 náhody: 671×
- neporáží spouštěč o 0,05 R: 568×
- OOS t < 2: 556×
- HOLDOUT ≤ 0: 242×
- OOS ≤ 0: 81×
- IS ≤ 0: 62×
- málo obchodů: 25×
- reg: bez zlepšení v IS: 1×

## Plán studie

Páry spouštěč + 1 filtr (každý TF ve dvou skupinách filtrů) → nejlepší páry podle IS + druhý filtr → citlivost sousedních parametrů spouštěče. Pak znovu na čerstvých datech. Funding/OI zatím chybí historická data.

Povyšování a vyřazování combo strategií dělá laboratoř (`research/lab.py`) podle papírových výsledků.
