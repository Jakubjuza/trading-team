# 🤖 AI Lab – strategie vymyšlené AI

Přepočet 2026-11-10T09:47+00:00. Pravidla stanovená předem jsou v hlavičce `research/ai_lab.py`. Jen papír, odděleno od desku; nejde o finanční poradenství.

| Strategie | Typ | IS | OOS | HOLDOUT | Výsledek | Účet od 2024 |
|---|---|---|---|---|---|---|
| Ozvěna BTC | vlastní nápad | -0,038 R (t -1,89, n 2487) | 0,127 R (t 2,61, n 644) | -0,143 R (t -3,16, n 273) | ❌ neprojde | 313,09 USDT |
| Tichý průraz | vlastní nápad | 0,113 R (t 1,3, n 459) | 0,185 R (t 1,07, n 137) | -0,11 R (t -0,75, n 150) | ❌ neprojde | -26,53 USDT |
| Hodiny trhu | vlastní nápad | Sharpe -1,06 | Sharpe -3,74 | Sharpe -6,19 | ❌ neprojde | -780,14 USDT |
| Rotace síly | vlastní nápad | Sharpe 1,05 | Sharpe -0,69 | Sharpe -2,04 | ❌ neprojde | -602,41 USDT |
| Evoluce · vítěz | evoluce | 0,203 R (t 6,8, n 2491) | 0,117 R (t 2,62, n 844) | 0,058 R (t 0,99, n 708) | ✅ projde | 1201,8 USDT |

## Evoluce

Vyzkoušeno 4340 pravidel (populace 200, 30 generací, fitness jen z let 2019–2023). Z 30 nejlepších v učení prošlo ověřením 6; z 30 náhodných pravidel stejné stavby 0.

Vítěz: LONG když stažení ATR14/200 > 60. percentil (0.99) a od EMA200 (ATR) > 70. percentil (2.54) a den v týdnu < 80. percentil (5.00) · stop 3,0 ATR · držení 32 h

| Pravidlo | fitness IS | OOS Ø R (t) | HOLDOUT Ø R (t) |
|---|---|---|---|
| LONG když od EMA200 (ATR) > 50. percentil a stažení ATR14/200 > 70. percentil a stažení ATR14/200 > 50. percentil · stop 3,0 ATR · držení 32 h | 6,53 | 0,074 (2,05) | -0,005 (-0,12) |
| LONG když stažení ATR14/200 > 60. percentil a stažení ATR14/200 > 70. percentil a od EMA200 (ATR) > 50. percentil · stop 3,0 ATR · držení 32 h | 6,53 | 0,074 (2,05) | -0,005 (-0,12) |
| LONG když stažení ATR14/200 > 70. percentil a stažení ATR14/200 > 70. percentil a od EMA200 (ATR) > 50. percentil · stop 3,0 ATR · držení 32 h | 6,53 | 0,074 (2,05) | -0,005 (-0,12) |
| LONG když od EMA200 (ATR) > 30. percentil a stažení ATR14/200 > 70. percentil · stop 3,0 ATR · držení 32 h | 6,5 | 0,029 (0,97) | -0,025 (-0,75) |
| LONG když stažení ATR14/200 > 60. percentil a od EMA200 (ATR) > 70. percentil a den v týdnu < 80. percentil · stop 3,0 ATR · držení 32 h | 6,5 | 0,117 (2,62) | 0,058 (0,99) |
| LONG když od EMA200 (ATR) > 50. percentil a od EMA200 (ATR) > 50. percentil a stažení ATR14/200 > 70. percentil · stop 3,0 ATR · držení 16 h | 6,48 | 0,031 (1,47) | -0,019 (-0,84) |
| LONG když stažení ATR14/200 > 60. percentil a od EMA200 (ATR) > 50. percentil · stop 3,0 ATR · držení 32 h | 6,47 | 0,043 (1,31) | 0,003 (0,07) |
| LONG když RSI 14 > 40. percentil a výnos 4 h (σ) > 90. percentil a od EMA200 (ATR) > 70. percentil · stop 3,0 ATR · držení 32 h | 6,43 | 0,112 (2,53) | 0,065 (1,17) |
| LONG když stažení ATR14/200 > 70. percentil a od EMA200 (ATR) > 40. percentil · stop 3,0 ATR · držení 32 h | 6,42 | 0,053 (1,61) | -0,013 (-0,35) |
| LONG když stažení ATR14/200 > 70. percentil a od EMA200 (ATR) > 30. percentil a stažení ATR14/200 > 70. percentil · stop 3,0 ATR · držení 32 h | 6,4 | 0,029 (0,97) | -0,025 (-0,75) |

## Průběžný výzkum (kola evoluce)

Kol celkem 2, strategií z kol 0/10, další zaměření: rychlé obchody 2–8 h.

| Kolo | Datum | Zaměření | Vyzkoušeno | Prošlo ověřením (náhoda) | Výsledek |
|---|---|---|---|---|---|
| 2 | 2026-11-10 | jen short | 4663 | 3 (0) | žádné pravidlo neprošlo přísným testem |
| 1 | 2026-11-09 | vše | 4204 | 22 (1) | žádné pravidlo neprošlo přísným testem |
