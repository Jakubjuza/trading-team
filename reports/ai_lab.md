# 🤖 AI Lab – strategie vymyšlené AI

Přepočet 2026-11-20T09:59+00:00. Pravidla stanovená předem jsou v hlavičce `research/ai_lab.py`. Jen papír, odděleno od desku; nejde o finanční poradenství.

| Strategie | Typ | IS | OOS | HOLDOUT | Výsledek | Účet od 2024 |
|---|---|---|---|---|---|---|
| Ozvěna BTC | vlastní nápad | -0,038 R (t -1,89, n 2487) | 0,127 R (t 2,61, n 644) | -0,145 R (t -3,26, n 282) | ❌ neprojde | 286,76 USDT |
| Tichý průraz | vlastní nápad | 0,113 R (t 1,3, n 459) | 0,185 R (t 1,07, n 137) | -0,11 R (t -0,75, n 150) | ❌ neprojde | -26,53 USDT |
| Hodiny trhu | vlastní nápad | Sharpe -1,06 | Sharpe -3,74 | Sharpe -6,35 | ❌ neprojde | -789,3 USDT |
| Rotace síly | vlastní nápad | Sharpe 1,05 | Sharpe -0,69 | Sharpe -2,04 | ❌ neprojde | -607,41 USDT |
| Evoluce · vítěz | evoluce | 0,203 R (t 6,8, n 2491) | 0,117 R (t 2,62, n 844) | 0,056 R (t 0,96, n 709) | ✅ projde | 1179,37 USDT |
| AI #3 · rychlé obchody 2–8 h | evoluce · kolo 3 | 0,078 R (t 6,02, n 2222) | 0,068 R (t 2,95, n 599) | 0,075 R (t 2,45, n 375) | ✅ projde | 885,65 USDT |
| AI #4 · pomalé obchody 16–32 h | evoluce · kolo 4 | 0,2 R (t 6,8, n 3031) | 0,113 R (t 2,55, n 989) | 0,063 R (t 1,15, n 829) | ✅ projde | 1452,65 USDT |
| AI #5 · jen long | evoluce · kolo 5 | 0,181 R (t 7,02, n 3684) | 0,116 R (t 2,95, n 1186) | 0,057 R (t 1,16, n 951) | ✅ projde | 1988,19 USDT |
| AI #6 · vše | evoluce · kolo 6 | 0,179 R (t 6,72, n 3551) | 0,115 R (t 2,87, n 1149) | 0,082 R (t 1,6, n 911) | ✅ projde | 2465,95 USDT |
| AI #8 · rychlé obchody 2–8 h | evoluce · kolo 8 | 0,089 R (t 7,05, n 2456) | 0,065 R (t 2,52, n 610) | 0,057 R (t 1,85, n 396) | ✅ projde | 762,1 USDT |
| AI #10 · jen long | evoluce · kolo 10 | 0,113 R (t 7,06, n 4602) | 0,098 R (t 4,13, n 1484) | 0,047 R (t 1,59, n 1137) | ✅ projde | 3757,55 USDT |
| AI #11 · vše | evoluce · kolo 11 | 0,191 R (t 7,07, n 3059) | 0,118 R (t 2,83, n 986) | 0,057 R (t 1,1, n 827) | ✅ projde | 1609,01 USDT |

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

Kol celkem 12, strategií z kol 7/10, další zaměření: rychlé obchody 2–8 h.

| Kolo | Datum | Zaměření | Vyzkoušeno | Prošlo ověřením (náhoda) | Výsledek |
|---|---|---|---|---|---|
| 12 | 2026-11-20 | jen short | 4620 | 9 (0) | žádné pravidlo neprošlo přísným testem |
| 11 | 2026-11-19 | vše | 4388 | 12 (0) | přidáno |
| 10 | 2026-11-18 | jen long | 4229 | 20 (0) | přidáno |
| 9 | 2026-11-17 | pomalé obchody 16–32 h | 3900 | 7 (1) | žádné pravidlo neprošlo přísným testem |
| 8 | 2026-11-16 | rychlé obchody 2–8 h | 4758 | 20 (0) | přidáno |
| 7 | 2026-11-15 | jen short | 4754 | 8 (0) | žádné pravidlo neprošlo přísným testem |
| 6 | 2026-11-14 | vše | 4340 | 20 (0) | přidáno |
| 5 | 2026-11-13 | jen long | 4277 | 17 (0) | přidáno |
| 4 | 2026-11-12 | pomalé obchody 16–32 h | 4282 | 8 (1) | přidáno |
| 3 | 2026-11-11 | rychlé obchody 2–8 h | 4677 | 17 (0) | přidáno |
| 2 | 2026-11-10 | jen short | 4663 | 3 (0) | žádné pravidlo neprošlo přísným testem |
| 1 | 2026-11-09 | vše | 4204 | 22 (1) | žádné pravidlo neprošlo přísným testem |
