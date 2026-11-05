# 🚧 Brána směru podle stavu trhu – výsledky testu

Spuštěno 2026-11-05 19:46 UTC · 26 aktivních strategií × 8 mincí · 72349 obchodů (65364 long, 6985 short) · 1106 s.
Pravidla předem (hlavička `research/experiments/long_gate.py`). IS < 2024-01 ≤ OOS < 2025-07 ≤ HOLDOUT.

| brána | blokuje | OOS: ponech. / blok. Ø R (n blok.) | HOLDOUT: ponech. / blok. Ø R (n blok.) | blok. OOS+H Ø R | rozdíl (t) | posl. 180 dní ponech. / blok. (n) | verdikt |
|---|---|---|---|---|---|---|---|
| G1 long | režim BTC medvědí | +0,409 / +0,280 (701) | +0,366 / +0,226 (3045) | +0,236 | +0,155 (+0,5) | +0,774 / +0,610 (1510) | NEPROŠLO ❌ |
| G2 long | křehký trh (K ≥ +0,25) | +0,432 / +0,134 (1382) | +0,378 / +0,050 (1749) | +0,087 | +0,319 (+1,1) | +0,829 / +0,080 (663) | NEPROŠLO ❌ |
| G3 long | G1 nebo G2 | +0,425 / +0,249 (1802) | +0,405 / +0,180 (4059) | +0,201 | +0,216 (+0,7) | +0,839 / +0,506 (1624) | NEPROŠLO ❌ |
| S1 short | režim BTC býčí | +0,387 / +0,277 (706) | +0,206 / +0,076 (315) | +0,215 | +0,052 (+0,3) | +0,249 / +0,002 (172) | NEPROŠLO ❌ |
| S2 short | optimistický trh (K ≤ −0,25) | +0,360 / +0,246 (345) | +0,207 / +0,059 (287) | +0,161 | +0,111 (+0,6) | +0,208 / +0,075 (108) | NEPROŠLO ❌ |
| S3 short | S1 nebo S2 | +0,355 / +0,315 (821) | +0,202 / +0,127 (465) | +0,247 | +0,004 (+0,0) | +0,252 / +0,069 (244) | NEPROŠLO ❌ |

Po strategiích – longy, Ø R v OOS+HOLDOUT podle režimu BTC:

| strategie | býčí | boční | medvědí | panika |
|---|---|---|---|---|
| Bollinger průraz 20 2.5 · 4H long | +0,710 (385) | +0,773 (165) | +0,284 (126) | -0,426 (110) |
| Bollinger průraz 20 2.5 · 6H long | +0,989 (274) | +0,700 (102) | +0,362 (82) | -0,236 (69) |
| Kombinace: Bollinger průraz 20 2.5 + trend EMA100 · 1H long | +0,277 (923) | +0,732 (305) | +0,051 (256) | -0,137 (137) |
| Donchian průraz 100 · 1H long | +0,353 (1421) | +0,462 (399) | +0,035 (318) | -0,141 (184) |
| Donchian průraz 20 · 6H long | +1,086 (527) | +0,599 (73) | +1,731 (20) | -0,477 (58) |
| Keltner průraz 2.5 · 6H long | +0,678 (237) | +0,651 (34) | +2,156 (13) | -0,511 (12) |
| Protnutí průměrů ema 5 50 pullback · 1H long | +0,374 (4507) | +0,804 (800) | +2,643 (175) | -0,185 (564) |
| Protnutí průměrů ema 50 60 cross · 6H long | +0,416 (93) | +0,322 (38) | +0,255 (30) | +0,410 (7) |
| Protnutí průměrů sma 30 60 cross · 4H long | +0,263 (169) | +0,078 (73) | +0,608 (76) | +0,211 (56) |
| MACD 19 39 9 signal · 12H long | +1,027 (158) | +0,261 (87) | +0,214 (96) | -0,137 (110) |
| MACD 19 39 9 signal · 2H long | +0,285 (1025) | +0,329 (458) | -0,087 (627) | +0,226 (211) |
| Cena × průměr ema 200 · 4H long | +0,848 (380) | +0,595 (213) | +0,472 (154) | -0,368 (147) |
| RSI momentum 60 · 2H long | +0,194 (1649) | +0,294 (613) | +0,143 (679) | -0,067 (274) |
| RSI momentum 60 · 4H long | +0,507 (806) | +0,407 (300) | +0,340 (279) | -0,335 (153) |
| RSI momentum 60 · 6H long | +0,636 (536) | +0,427 (198) | -0,016 (168) | -0,345 (83) |
| Průraz s objemem 20 1.5 · 6H long | +1,682 (336) | +0,925 (51) | +0,821 (14) | -0,448 (33) |
| Průraz s objemem 20 2.5 · 12H long | +0,711 (71) | +0,085 (15) | -0,254 (13) | -1,010 (5) |
| Průraz s objemem 55 1.5 · 1H long | +0,335 (1206) | +0,398 (428) | -0,048 (371) | -0,062 (175) |
| Průraz s objemem 55 2.5 · 1H long | +0,310 (703) | +0,508 (300) | -0,007 (249) | -0,166 (223) |

Prošlé brány použije papír laboratoře (zablokovaný signál jde stínově a měří se dál). Neprošlé se nepoužijí.

Nejde o finanční poradenství.
