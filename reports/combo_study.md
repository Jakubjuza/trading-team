# 🧩 Studie kombinací ukazatelů, signálů a spouštěčů

Průběžná studie: spouštěč z atlasu + 1–2 potvrzení/filtry z jiných rodin nebo kontextu. Metoda, filtry a pravidla jsou stanoveny předem v hlavičce `research/experiments/combo_study.py`; data, náklady (MEXC 0,05 %/stranu), simulace a dělení IS (do 12/2023) / OOS (1/2024–6/2025) / HOLDOUT (7/2025–) jsou stejné jako v atlasu. Papírově, nic nejde na skutečné peníze. Nejde o finanční poradenství.

- Hotových dílů: **1**, testovaných kombinací celkem (vč. samotných spouštěčů): **144** – při tolika testech projde pravidlem i něco čistě náhodou, proto jen papír.
- Poslední díl 1: **pair 1H** (skupiny trend, režim, objem), 132 kombinací + 12 spouštěčů samotných, 3 s; základní pravidlo splnilo 9, prošlo vč. citlivosti a režimů 8.
- Mřížka (stanovena před výpočtem): spouštěče ma_cross sma/30/200/confirm · opp · long; macd 19/39/9/zero · opp · long; donchian 100 · opp · long; boll_break 20/2.5 · opp · long; price_ma sma/100 · opp_stop · long; supertrend 20/3.0 · opp · long; ma_cross sma/50/100/pullback · trail · short; boll_break 50/2.0 · target · short; price_ma sma/100 · trail · short; macd 19/39/9/zero · trail · short; vol_break 55/2.5 · target · short; donchian 100 · trail · short × filtry ema:50, ema:100, ema:200, d:50, d:200, reg:trend, reg:notpanic, reg:side, vol:1, vol:1.5, vol:2.
- Další díl: **pair 1H** (skupiny volatilita, momentum, sentiment).

## Změny v registru v tomto běhu

- 🆕 Kombinace: Bollinger průraz 20 2.5 + trend EMA100 · 1H long → papír (combo_study: díl 1, OOS +0.18 R (t +2.6), HOLDOUT +0.33 R (t +2.3), spouštěč sám OOS +0.11 R); režimy: býčí, medvědí, boční
- 🆕 Kombinace: Průraz s objemem 55 2.5 + režim side · 1H short → papír (combo_study: díl 1, OOS +0.23 R (t +2.1), HOLDOUT +0.23 R (t +2.2), spouštěč sám OOS +0.09 R); režimy: boční

## Combo strategie v registru (2 aktivních, limit 10)

| Strategie | Stav | OOS Ø R (t) | HOLDOUT Ø R (t) | Spouštěč sám OOS | Režimy | Papír |
|---|---|---|---|---|---|---|
| Kombinace: Bollinger průraz 20 2.5 + trend EMA100 · 1H long | papír | +0,18 (+2,6) | +0,33 (+2,3) | +0,11 | býčí, medvědí, boční | 0 obch., Ø – R |
| Kombinace: Průraz s objemem 55 2.5 + režim side · 1H short | papír | +0,23 (+2,1) | +0,23 (+2,2) | +0,09 | boční | 0 obch., Ø – R |

## Top 10 kombinací (podle min(OOS t, HOLDOUT t), všechny díly)

| Díl | TF | Kombinace | Výstup · směr | IS Ø R (t) | OOS Ø R (t) | HOLDOUT Ø R (t) | p95 náhody OOS / HOLD | Spouštěč sám OOS | Obchodů IS/OOS/HOLD | Výsledek |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1H | Bollinger průraz 20 2.5 + trend EMA100 | opp · long | +0,28 (+5,7) | +0,18 (+2,6) | +0,33 (+2,3) | +0,10 / +0,14 | +0,11 | 2334/761/629 | ✅ prošlo |
| 1 | 1H | Bollinger průraz 20 2.5 + objem×2 | opp · long | +0,25 (+5,2) | +0,14 (+2,2) | +0,27 (+2,5) | +0,02 / +0,08 | +0,11 | 2418/816/803 | ❌ neporáží spouštěč o 0,05 R |
| 1 | 1H | Průraz s objemem 55 2.5 + režim side | target · short | +0,11 (+1,6) | +0,23 (+2,1) | +0,23 (+2,2) | +0,17 / +0,04 | +0,09 | 328/133/134 | ✅ prošlo |
| 1 | 1H | Bollinger průraz 20 2.5 + objem×1 | opp · long | +0,19 (+5,0) | +0,12 (+2,2) | +0,18 (+2,1) | +0,03 / +0,06 | +0,11 | 3433/1105/1078 | ❌ neporáží spouštěč o 0,05 R |
| 1 | 1H | Bollinger průraz 20 2.5 + režim notpanic | opp · long | +0,16 (+4,1) | +0,18 (+2,7) | +0,18 (+2,0) | +0,07 / +0,09 | +0,11 | 2794/830/1079 | ❌ reg: bez zlepšení v IS |
| 1 | 1H | Bollinger průraz 20 2.5 + objem×1,5 | opp · long | +0,22 (+5,2) | +0,12 (+2,0) | +0,22 (+2,2) | +0,03 / +0,08 | +0,11 | 2950/988/966 | ❌ OOS t < 2, neporáží spouštěč o 0,05 R |
| 1 | 1H | Bollinger průraz 20 2.5 + denní 50 | opp · long | +0,31 (+5,6) | +0,16 (+1,9) | +0,25 (+2,0) | +0,05 / +0,20 | +0,11 | 1879/551/461 | ❌ OOS t < 2, neporáží spouštěč o 0,05 R |
| 1 | 1H | Bollinger průraz 20 2.5 + trend EMA50 | opp · long | +0,28 (+5,9) | +0,18 (+2,7) | +0,22 (+1,8) | +0,10 / +0,12 | +0,11 | 2574/848/748 | ✅ prošlo |
| 1 | 1H | Bollinger průraz 20 2.5 + trend EMA200 | opp · long | +0,33 (+6,3) | +0,19 (+2,6) | +0,20 (+1,8) | +0,07 / +0,12 | +0,11 | 2167/684/595 | ✅ prošlo |
| 1 | 1H | Supertrend 20 3.0 + trend EMA100 | opp · long | +0,51 (+4,8) | +0,26 (+1,9) | +0,27 (+1,8) | +0,12 / +0,31 | +0,23 | 1168/366/335 | ❌ pod p95 náhody, OOS t < 2, neporáží spouštěč o 0,05 R |

## Co filtry dělají se spouštěči (páry, průměr přes spouštěče)

| TF | Filtr | Spouštěčů | Ø zlepšení IS | Ø zlepšení OOS | Podíl OOS zlepšení > 0 | Splnilo základní pravidlo |
|---|---|---|---|---|---|---|
| 1H | d:200 | 9 | +0,09 | -0,03 | 42% | 0 |
| 1H | d:50 | 9 | +0,18 | -0,04 | 25% | 0 |
| 1H | ema:100 | 9 | +0,08 | -0,00 | 42% | 1 |
| 1H | ema:200 | 9 | +0,10 | +0,02 | 42% | 2 |
| 1H | ema:50 | 9 | -0,01 | -0,01 | 33% | 1 |
| 1H | reg:notpanic | 9 | -0,00 | +0,14 | 100% | 4 |
| 1H | reg:side | 9 | -0,06 | +0,04 | 58% | 1 |
| 1H | reg:trend | 9 | +0,17 | +0,15 | 83% | 0 |
| 1H | vol:1 | 9 | +0,04 | -0,02 | 42% | 0 |
| 1H | vol:1.5 | 9 | +0,06 | -0,04 | 42% | 0 |
| 1H | vol:2 | 9 | +0,08 | -0,01 | 50% | 0 |

## Proč neprošly (nejčastější důvody)

- pod p95 náhody: 108×
- OOS t < 2: 99×
- neporáží spouštěč o 0,05 R: 96×
- HOLDOUT ≤ 0: 36×
- OOS ≤ 0: 11×
- IS ≤ 0: 3×
- reg: bez zlepšení v IS: 1×

## Plán studie

Páry spouštěč + 1 filtr (každý TF ve dvou skupinách filtrů) → nejlepší páry podle IS + druhý filtr → citlivost sousedních parametrů spouštěče. Pak znovu na čerstvých datech. Funding/OI zatím chybí historická data.

Povyšování a vyřazování combo strategií dělá laboratoř (`research/lab.py`) podle papírových výsledků.
