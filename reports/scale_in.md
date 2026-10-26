# Dokupování při poklesu s malou pákou, řez části ztráty, znovuotevření a držení po obratu (26. 10. 2026)

Předem stanovený test (`research/experiments/scale_in.py`, běh v GitHub Actions, denní svíčky, 8 mincí, 2017–2026).
Spouštěč: close ≥ 20 % pod 30denním maximem. Testovací kus 0,25 účtu, dokup kusu každých −5 % od posledního nákupu
(max. 6 kusů = 1,5 × účet). V1/V2: při −15 % pod průměrnou cenou prodat polovinu; V1 koupit zpět o 5 % níž, V2 koupit
zpět při návratu na cenu řezu. Po návratu nad průměrnou cenu trailing 3 ATR, max. 365 dní. Náklady 0,1 %/plnění,
půjčka 10 % p.a. B1 = jeden nákup 1 × účet bez dokupů, stejný výstup. Každá mince podúčet 1 000 USD (portfolio 8 000).

Buy & hold portfolio: **345 180 USD**, CAGR +46 %, max. propad 88 %.

| Varianta | Stop kampaně | Kampaní | Úspěšnost | Ø kampaň | Nejhorší | IS / OOS | Náhodné starty | Portfolio konec | CAGR | Max. propad |
|---|---|---|---|---|---|---|---|---|---|---|
| B1 jeden nákup | bez | 373 | 40 % | +18,7 % | −96 % | +26,2 / +1,0 % | +20,3 % | 163 942 | +35 % | 79 % |
| V0 jen dokupovat | bez | 467 | 45 % | +10,9 % | −97 % | +15,4 / +0,3 % | +10,5 % | 62 285 | +23 % | 75 % |
| V1 řez + znovu níž | bez | 482 | 44 % | +10,0 % | −74 % | +14,3 / +0,0 % | +10,3 % | 44 636 | +19 % | 73 % |
| V2 řez + znovu na místě | bez | 482 | 43 % | +10,0 % | −97 % | +14,7 / −1,0 % | +9,2 % | 54 823 | +21 % | 77 % |
| B1 | −20 % | 591 | 33 % | +12,0 % | −20 % | +16,3 / +1,9 % | +12,3 % | 122 408 | +31 % | 79 % |
| V0 = V1 = V2 | −20 % | 553 | 39 % | +7,0 % | −20 % | +10,1 / −0,4 % | +6,7 až +10,9 % | 53 143 | +21 % | 70 % |
| B1 | −35 % | 486 | 36 % | +14,1 % | −35 % | +20,2 / −0,3 % | +13,5 % | 61 489 | +23 % | 81 % |
| V0 | −35 % | 517 | 42 % | +7,2 % | −35 % | +10,3 / +0,1 % | +13,0 % | 21 353 | +10 % | 84 % |
| V1 | −35 % | 508 | 42 % | +8,6 % | −35 % | +12,2 / +0,2 % | +6,6 % | 18 515 | +9 % | 78 % |
| V2 | −35 % | 504 | 42 % | +10,0 % | −40 % | +14,4 / −0,0 % | +8,7 % | 86 650 | +27 % | 79 % |

Likvidace: V0 bez stopu 3×, V2 bez stopu 1×. Se stopem −20 % jsou V0–V2 totožné – při plné pozici 1,5× a ceně
−15 % pod průměrem je ztráta ≈ 22 % účtu, stop kampaně tedy vždy přijde dřív než první řez.
Po letech (V1, Ø kampaň): 2018 −8 % · 2020 +99 % · 2021 +18 % · 2022 −4 % · 2025 −0 % · 2026 −2 %.
Nejhorší kampaně V1: ADA 1/2018 −74 % (6 řezů), ADA 3/2018 −59 %, SOL 11/2022 −56 %, AVAX 5/2022 −54 %.

## Závěr

❌ **Neprošlo žádné z 9 nastavení.** Dokupování do ztráty dalo zhruba **polovinu výsledku jednoho nákupu**
(Ø +10 % vs. +18,7 % na kampaň) a nebylo lepší než stejná pravidla z náhodného dne (+10,3 %) – kladné průměry dělá
růst krypta 2017–2021, ne pravidla. Za posledních 30 % kampaní (OOS) je všechno kolem nuly. Propad portfolia byl
o něco menší než u buy & hold (73–77 % vs. 88 %), ale konečný stav 5–8× nižší.

Řez a znovuotevření nepomohlo: průměrná cena zbylé pozice sice klesne, ale ztráta z prodeje zůstává realizovaná
a v dlouhém propadu (2018, 2022) se řeže a kupuje znovu opakovaně (až 6 řezů v jedné kampani).
Pro srovnání: přikupování do **zisku** testem prošlo (`reports/pyramid.md`) – směr dokupování je podstatný.

Nejde o finanční poradenství.
