# 💰 $1M Future – simulace dvou let Agentownu

Přepočet 2026-11-09T20:47+00:00 · `research/future_lab.py` (pravidla stanovená předem v hlavičce skriptu). Jen papír, ne rada.

## A) Stroj času zpět (od 9. 11. 2024)

24 měsíčních kol, vyzkoušeno 46395 pravidel. Strategie obchodují jen od přidání (data, která v době rozhodnutí nikdo neviděl).

Fond A (riziko 0.5 %/obchod): 46.45 USD (-95,4 %), max. propad -99.4 %, obchodů 8374, Ø R +0,021 (t +1,30). BTC drž: -2,3 %.

| kolo | datum | zaměření | ověřením / náhodných | výsledek |
|---|---|---|---|---|
| 1 | 2024-11-09 | vše | 7 / 0 | přidáno |
| 2 | 2024-12-09 | jen short | 0 / 0 | kolo neporazilo náhodnou kontrolu (0 × 0) |
| 3 | 2025-01-09 | rychlé obchody 2–8 h | 7 / 0 | přidáno |
| 4 | 2025-02-09 | pomalé obchody 16–32 h | 22 / 0 | přidáno |
| 5 | 2025-03-09 | jen long | 12 / 0 | přidáno |
| 6 | 2025-04-09 | vše | 12 / 0 | přidáno |
| 7 | 2025-05-09 | jen short | 0 / 0 | kolo neporazilo náhodnou kontrolu (0 × 0) |
| 8 | 2025-06-09 | rychlé obchody 2–8 h | 7 / 0 | přidáno |
| 9 | 2025-07-09 | pomalé obchody 16–32 h | 28 / 2 | přidáno |
| 10 | 2025-08-09 | jen long | 29 / 3 | přidáno |
| 11 | 2025-09-09 | vše | 18 / 0 | přidáno |
| 12 | 2025-10-09 | jen short | 0 / 0 | kolo neporazilo náhodnou kontrolu (0 × 0) |
| 13 | 2025-11-09 | rychlé obchody 2–8 h | 16 / 0 | přidáno |
| 14 | 2025-12-09 | pomalé obchody 16–32 h | 1 / 0 | nic neprošlo testem |
| 15 | 2026-01-09 | jen long | 2 / 0 | nic neprošlo testem |
| 16 | 2026-02-09 | vše | 3 / 0 | nic neprošlo testem |
| 17 | 2026-03-09 | jen short | 8 / 0 | přidáno místo slabší |
| 18 | 2026-04-09 | rychlé obchody 2–8 h | 0 / 0 | kolo neporazilo náhodnou kontrolu (0 × 0) |
| 19 | 2026-05-09 | pomalé obchody 16–32 h | 0 / 0 | kolo neporazilo náhodnou kontrolu (0 × 0) |
| 20 | 2026-06-09 | jen long | 0 / 0 | kolo neporazilo náhodnou kontrolu (0 × 0) |
| 21 | 2026-07-09 | vše | 0 / 0 | kolo neporazilo náhodnou kontrolu (0 × 0) |
| 22 | 2026-08-09 | jen short | 0 / 0 | kolo neporazilo náhodnou kontrolu (0 × 0) |
| 23 | 2026-09-09 | rychlé obchody 2–8 h | 0 / 0 | kolo neporazilo náhodnou kontrolu (0 × 0) |
| 24 | 2026-10-09 | pomalé obchody 16–32 h | 0 / 0 | kolo neporazilo náhodnou kontrolu (0 × 0) |

| strategie | přidána | vyřazena | ověření t při přidání | po přidání Ø R (t, n) | účet |
|---|---|---|---|---|---|
| Budoucí #1 · vše | 2024-11-09 | 2026-03-09 | +2,69 | +0,116 (+2,36, 667) | 1767.14 |
| Budoucí #3 · rychlé obchody 2–8 h | 2025-01-09 | – | +4,62 | +0,010 (+0,57, 752) | 1025.03 |
| Budoucí #4 · pomalé obchody 16–32 h | 2025-02-09 | – | +3,03 | +0,001 (+0,01, 1543) | 293.82 |
| Budoucí #5 · jen long | 2025-03-09 | – | +3,45 | +0,079 (+1,57, 952) | 1293.53 |
| Budoucí #6 · vše | 2025-04-09 | – | +3,52 | +0,038 (+0,84, 1054) | 908.93 |
| Budoucí #8 · rychlé obchody 2–8 h | 2025-06-09 | – | +3,22 | +0,021 (+0,82, 563) | 1080.5 |
| Budoucí #9 · pomalé obchody 16–32 h | 2025-07-09 | – | +3,91 | +0,073 (+1,30, 677) | 1197.84 |
| Budoucí #10 · jen long | 2025-08-09 | – | +4,74 | -0,007 (-0,12, 719) | 666.76 |
| Budoucí #11 · vše | 2025-09-09 | – | +3,73 | -0,048 (-0,71, 791) | 382.24 |
| Budoucí #13 · rychlé obchody 2–8 h | 2025-11-09 | – | +4,04 | -0,031 (-1,39, 508) | 836.05 |
| Budoucí #17 · jen short | 2026-03-09 | – | +3,43 | -0,191 (-1,64, 148) | 714.23 |

## B) Zrychlená budoucnost (výzkum do 2025-11-09, závěrečný test potom)

48 kol, vyzkoušeno 92746 pravidel, kol nad náhodou 47, prošlo 132 kandidátů, vybráno 10.

Fond B na závěrečném testu: 12.15 USD (-98,8 %), max. propad -99.0 %, Ø R -0,076 (t -5,50, n 6112). BTC drž: -28,5 %.

| strategie | pravidlo | ověření Ø R (t) | závěrečný test Ø R (t, n) |
|---|---|---|---|
| Future #1 · rychlé obchody 2–8 h | LONG když od EMA200 (ATR) > 80. percentil (3.93) a hodina UTC > 80. percentil (19.00) a stažení ATR14/200 > 30. percentil (0.79) · stop 3,0 ATR · držení 8 h | +0,115 (+4,03) | -0,089 (-2,97, 407) |
| Future #2 · jen long | LONG když BTC 1 h (σ) < 20. percentil (-0.56) a hodina UTC > 50. percentil (12.00) a od EMA200 (ATR) > 60. percentil (1.21) · stop 3,0 ATR · držení 16 h | +0,111 (+4,00) | -0,144 (-4,70, 840) |
| Future #3 · rychlé obchody 2–8 h | LONG když od EMA50 (ATR) > 90. percentil (2.91) a hodina UTC > 50. percentil (12.00) a BTC 1 h (σ) < 20. percentil (-0.56) · stop 3,0 ATR · držení 8 h | +0,175 (+3,86) | -0,066 (-1,29, 212) |
| Future #4 · jen long | LONG když hodina UTC > 60. percentil (14.00) a od EMA200 (ATR) > 70. percentil (2.51) · stop 3,0 ATR · držení 16 h | +0,111 (+3,81) | -0,100 (-3,21, 821) |
| Future #5 · jen long | LONG když od EMA50 (ATR) > 10. percentil (-2.49) a od EMA200 (ATR) > 70. percentil (2.51) a hodina UTC > 60. percentil (14.00) · stop 3,0 ATR · držení 16 h | +0,111 (+3,81) | -0,100 (-3,21, 821) |
| Future #6 · jen long | LONG když hodina UTC > 60. percentil (14.00) a od EMA200 (ATR) > 70. percentil (2.51) a den v týdnu < 90. percentil (6.00) · stop 3,0 ATR · držení 16 h | +0,116 (+3,70) | -0,122 (-3,97, 688) |
| Future #7 · vše | LONG když od EMA200 (ATR) > 70. percentil (2.51) a stažení ATR14/200 > 70. percentil (1.08) · stop 3,0 ATR · držení 32 h | +0,194 (+3,51) | -0,002 (-0,03, 464) |
| Future #8 · vše | LONG když od EMA200 (ATR) > 70. percentil (2.51) a stažení ATR14/200 > 50. percentil (0.92) a výnos 1 h (σ) < 40. percentil (-0.16) · stop 3,0 ATR · držení 32 h | +0,183 (+3,50) | -0,074 (-1,09, 516) |
| Future #9 · pomalé obchody 16–32 h | LONG když od EMA200 (ATR) > 70. percentil (2.51) a stažení ATR14/200 > 70. percentil (1.08) a od EMA50 (ATR) > 20. percentil (-1.62) · stop 3,0 ATR · držení 32 h | +0,192 (+3,48) | -0,001 (-0,01, 462) |
| Future #10 · jen long | LONG když BTC 1 h (σ) < 30. percentil (-0.33) a od EMA50 (ATR) > 50. percentil (0.06) a od EMA200 (ATR) > 70. percentil (2.51) · stop 3,0 ATR · držení 16 h | +0,098 (+3,45) | -0,006 (-0,16, 881) |

„Cesta k $1M“ je jen přepočet tempa fondu, ne předpověď. Nejde o finanční poradenství.
