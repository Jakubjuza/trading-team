# 🧠 Mozek města – studie kupolí a nasazování podle fáze trhu

Přepočet 2026-11-08T18:42+00:00. Pravidla stanovená předem jsou v hlavičce `research/experiments/brain_study.py`. Jen papír; nic se nemění na skeneru, registru, riziku ani penězích. Nejde o finanční poradenství.

## Verdikt

**PROJDE: Mozek strategií**

- Mozek kupolí: Sharpe OOS ✅ · HOLDOUT ✅ · propad ✅ · nad 95. percentilem náhody (2,55) ✅
- Mozek strategií: Sharpe OOS ✅ · HOLDOUT ✅ · propad ✅ · nad 95. percentilem náhody (2,55) ✅

## Výsledky (test od 1. 1. 2024)

| Varianta | Sharpe test | OOS | HOLDOUT | roční výnos test | max. propad test | dnů s přesunem vah | vývoj 2020–23 Sharpe |
|---|---|---|---|---|---|---|---|
| Všechno pořád | 2,48 | 3,71 | 1,79 | 67,1 % | -23,9 % | – | 3,95 |
| Mozek kupolí | 2,64 | 3,73 | 2,02 | 73,1 % | -18,4 % | 95,8 % | 3,92 |
| Mozek strategií | 2,73 | 3,84 | 2,14 | 85,5 % | -16,5 % | 100,0 % | 4,06 |
| Držení BTC | 0,67 | 1,47 | -0,4 | 22,7 % | -53,0 % | – | 1,0 |

## Kupole (z období vývoje do 1. 1. 2024; mediány: propad 38,0 %, roční výnos 60,7 %)

**Pevnost** (9)
- čtvrť průraz: Bollinger průraz 20 2.5 · 6H long (-30,9 % / 123,8 %); Bollinger průraz 20 2.5 · 4H long (-34,9 % / 160,3 %); Donchian průraz 20 · 6H long (-29,5 % / 139,4 %); Průraz s objemem 20 1.5 · 6H long (-25,6 % / 115,5 %); Keltner průraz 2.5 · 6H long (-20,9 % / 90,5 %)
- čtvrť kombinace: Kombinace: Bollinger průraz 20 2.5 + ATR pctl ≥ 0,7 · 1H long (-38,0 % / 60,7 %); Kombinace: Bollinger průraz 50 2.5 + trend EMA200 · 2H long (-34,7 % / 295,4 %); Kombinace: Bollinger průraz 50 2.5 + denní 50 · 2H long (-32,0 % / 209,5 %)
- čtvrť jádro: Pyramida · přikupování (P2) (-23,1 % / 75,1 %)

**Spořitelna** (9)
- čtvrť trend: Protnutí průměrů ema 50 60 cross · 6H long (-25,9 % / 2,3 %); Supertrend 10 3.0 · 4H short (-31,8 % / 1,6 %)
- čtvrť průraz: Bollinger průraz 50 2.5 · 4H short (-23,5 % / 10,3 %); Průraz s objemem 20 2.5 · 12H long (-12,7 % / 13,9 %); Keltner průraz 2.5 · 4H short (-31,6 % / 2,8 %)
- čtvrť kombinace: Kombinace: Průraz s objemem 55 2.5 + režim side · 1H short (-25,5 % / 6,5 %)
- čtvrť jádro: Věž Donchian · průraz denního kanálu (-8,8 % / 16,2 %); Věž Pullback · návrat k trendu (-20,2 % / 8,9 %); Ensemble · trendová alokace (-25,6 % / 31,8 %)

**Motor** (9)
- čtvrť trend: MACD 19 39 9 signal · 12H long (-40,6 % / 135,3 %); MACD 19 39 9 signal · 2H long (-95,6 % / 107,8 %); Protnutí průměrů ema 5 50 pullback · 1H long (-69,3 % / 232,5 %); RSI momentum 60 · 4H long (-48,6 % / 289,3 %); RSI momentum 60 · 2H long (-70,2 % / 289,3 %); Cena × průměr ema 200 · 4H long (-52,6 % / 318,2 %); RSI momentum 60 · 6H long (-40,6 % / 221,6 %)
- čtvrť kombinace: Kombinace: Bollinger průraz 20 2.5 + trend EMA100 · 1H long (-54,2 % / 187,6 %); Kombinace: Bollinger průraz 20 2.5 + ATR pctl ≥ 0,3 · 1H long (-64,4 % / 107,5 %)

**Divočina** (8)
- čtvrť trend: Supertrend 10 3.0 · 6H short (-41,0 % / 0,6 %); Protnutí průměrů sma 20 50 cross · 2H short (-45,3 % / 3,2 %); Protnutí průměrů sma 30 60 cross · 4H long (-50,5 % / 2,3 %)
- čtvrť průraz: Donchian průraz 100 · 1H long (-76,1 % / 47,8 %); Průraz s objemem 55 1.5 · 1H long (-80,5 % / 31,4 %); Keltner průraz 2.5 · 2H short (-45,2 % / 2,6 %); Průraz s objemem 55 2.5 · 1H long (-48,8 % / 45,8 %)
- čtvrť návrat: Sweep & reclaim 55 · 4H long · boční (-79,2 % / -21,1 %)

**Nováček** (0)

## Kupole × fáze trhu v období vývoje (průměrný denní výnos v bazických bodech, počet dnů)

| Kupole | býk · pila · divoko | býk · pila · klid | býk · trend · divoko | býk · trend · klid | medvěd · pila · divoko | medvěd · pila · klid | medvěd · trend · divoko | medvěd · trend · klid |
|---|---|---|---|---|---|---|---|---|
| Pevnost | 33,1 (214) | 15,1 (340) | 79,1 (179) | 80,7 (184) | -2,7 (187) | 5,8 (256) | -2,7 (115) | 0,6 (151) |
| Spořitelna | 0,6 (214) | 1,1 (340) | 6,5 (179) | 4,9 (184) | -0,1 (187) | 1,2 (256) | 5,5 (115) | 8,8 (151) |
| Motor | 40,4 (214) | 28,2 (340) | 130,2 (179) | 107,8 (184) | -10,1 (187) | 11,8 (256) | -16,2 (115) | -7,2 (151) |
| Divočina | 1,4 (214) | 8,7 (340) | 16,2 (179) | 18,6 (184) | 0,6 (187) | 2,2 (256) | -18,5 (115) | -7,3 (151) |

## Dnes (jen ukázka, nic se nenasazuje): fáze býk · pila · klid

- Mozek kupolí – váhy kapitálu: Pevnost 25,0 %, Spořitelna 25,0 %, Motor 25,0 %, Divočina 25,0 %
- Mozek strategií: 22 strategií s vyšší vahou, 1 s nižší, ostatní základní.

Upozornění: strategie Laboratoře byly vybrané i podle OOS/HOLDOUT, absolutní čísla jsou proto optimistická; test měří, jestli přepínání přidává hodnotu proti stejnému vesmíru bez přepínání.
