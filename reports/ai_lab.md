# 🤖 AI Lab – strategie vymyšlené AI

Přepočet 2026-11-26T10:51+00:00. Pravidla stanovená předem jsou v hlavičce `research/ai_lab.py`. Jen papír, odděleno od desku; nejde o finanční poradenství.

| Strategie | Typ | IS | OOS | HOLDOUT | Výsledek | Účet od 2024 |
|---|---|---|---|---|---|---|
| Ozvěna BTC | vlastní nápad | -0,038 R (t -1,89, n 2487) | 0,127 R (t 2,61, n 644) | -0,148 R (t -3,34, n 283) | ❌ neprojde | 273,09 USDT |
| Tichý průraz | vlastní nápad | 0,113 R (t 1,3, n 459) | 0,185 R (t 1,07, n 137) | -0,11 R (t -0,75, n 150) | ❌ neprojde | -26,53 USDT |
| Hodiny trhu | vlastní nápad | Sharpe -1,06 | Sharpe -3,74 | Sharpe -6,33 | ❌ neprojde | -790,84 USDT |
| Rotace síly | vlastní nápad | Sharpe 1,05 | Sharpe -0,69 | Sharpe -2,17 | ❌ neprojde | -623,15 USDT |
| Evoluce · vítěz | evoluce | 0,203 R (t 6,8, n 2491) | 0,117 R (t 2,62, n 844) | 0,055 R (t 0,94, n 710) | ✅ projde | 1156,98 USDT |
| AI #3 · rychlé obchody 2–8 h | evoluce · kolo 3 | 0,078 R (t 6,02, n 2222) | 0,068 R (t 2,95, n 599) | 0,075 R (t 2,45, n 375) | ✅ projde | 885,65 USDT |
| AI #4 · pomalé obchody 16–32 h | evoluce · kolo 4 | 0,2 R (t 6,8, n 3031) | 0,113 R (t 2,55, n 989) | 0,059 R (t 1,08, n 832) | ✅ projde | 1376,9 USDT |
| AI #5 · jen long | evoluce · kolo 5 | 0,181 R (t 7,02, n 3684) | 0,116 R (t 2,95, n 1186) | 0,053 R (t 1,09, n 954) | ✅ projde | 1895,9 USDT |
| AI #6 · vše | evoluce · kolo 6 | 0,179 R (t 6,72, n 3551) | 0,115 R (t 2,87, n 1149) | 0,078 R (t 1,53, n 914) | ✅ projde | 2358,9 USDT |
| AI #8 · rychlé obchody 2–8 h | evoluce · kolo 8 | 0,089 R (t 7,05, n 2456) | 0,065 R (t 2,52, n 610) | 0,057 R (t 1,85, n 396) | ✅ projde | 762,1 USDT |
| AI #10 · jen long | evoluce · kolo 10 | 0,113 R (t 7,06, n 4602) | 0,098 R (t 4,13, n 1484) | 0,046 R (t 1,56, n 1138) | ✅ projde | 3708,88 USDT |
| AI #14 · pomalé obchody 16–32 h | evoluce · kolo 14 | 0,183 R (t 6,72, n 3452) | 0,126 R (t 3,08, n 1099) | 0,075 R (t 1,48, n 889) | ✅ projde | 2575,69 USDT |
| AI #15 · jen long | evoluce · kolo 15 | 0,207 R (t 7,48, n 3374) | 0,112 R (t 2,74, n 1098) | 0,073 R (t 1,4, n 894) | ✅ projde | 1987,29 USDT |
| AI #16 · vše | evoluce · kolo 16 | 0,212 R (t 6,91, n 3093) | 0,134 R (t 3,08, n 993) | 0,101 R (t 1,84, n 808) | ✅ projde | 3077,53 USDT |
| AI #18 · rychlé obchody 2–8 h | evoluce · kolo 18 | 0,092 R (t 6,95, n 2258) | 0,07 R (t 2,57, n 541) | 0,066 R (t 2,04, n 377) | ✅ projde | 780,07 USDT |

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

Kol celkem 18, strategií z kol 10/10, další zaměření: pomalé obchody 16–32 h.

| Kolo | Datum | Zaměření | Vyzkoušeno | Prošlo ověřením (náhoda) | Výsledek |
|---|---|---|---|---|---|
| 18 | 2026-11-26 | rychlé obchody 2–8 h | 4691 | 19 (0) | přidáno místo AI #17 · jen short |
| 17 | 2026-11-25 | jen short | 4397 | 10 (0) | přidáno místo AI #11 · vše |
| 16 | 2026-11-24 | vše | 4504 | 21 (0) | přidáno |
| 15 | 2026-11-23 | jen long | 4066 | 20 (0) | přidáno |
| 14 | 2026-11-22 | pomalé obchody 16–32 h | 3968 | 22 (1) | přidáno |
| 13 | 2026-11-21 | rychlé obchody 2–8 h | 4135 | 19 (0) | žádné pravidlo neprošlo přísným testem |
| 12 | 2026-11-20 | jen short | 4620 | 9 (0) | žádné pravidlo neprošlo přísným testem |
| 11 | 2026-11-19 | vše | 4388 | 12 (0) | přidáno |
| 10 | 2026-11-18 | jen long | 4229 | 20 (0) | přidáno |
| 9 | 2026-11-17 | pomalé obchody 16–32 h | 3900 | 7 (1) | žádné pravidlo neprošlo přísným testem |
| 8 | 2026-11-16 | rychlé obchody 2–8 h | 4758 | 20 (0) | přidáno |
| 7 | 2026-11-15 | jen short | 4754 | 8 (0) | žádné pravidlo neprošlo přísným testem |
| 6 | 2026-11-14 | vše | 4340 | 20 (0) | přidáno |
| 5 | 2026-11-13 | jen long | 4277 | 17 (0) | přidáno |
| 4 | 2026-11-12 | pomalé obchody 16–32 h | 4282 | 8 (1) | přidáno |
