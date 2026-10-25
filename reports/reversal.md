# Obrat po prudkém pohybu s těsným stopem + výzva „malý účet → velký“ (25. 10. 2026)

Předem stanovený test (`research/experiments/reversal.py`, běh v GitHub Actions, 15M svíčky OKX, 8 mincí, 10/2024–10/2026).
Prudký pohyb = cena se za 4 h pohne o ≥ 4 × ATR (1H). Vstup do 12 h: 15M svíčka zavře za max/min 2 předchozích
(obrat proti pohybu). Stop těsně za extrémem pohybu (min. 0,3 %). Jeden pokus na pohyb, max. 7 dní.

**1 177 pokusů** (562 long, 615 short). Stop od vstupu: medián 1,4 % (10.–90. percentil 0,7–3,0 %).

| Výstup (náklady 0,07 %/stranu – futures) | Úspěšnost | Ø R ± CI | ≥ 10R | ≥ 20R | ≥ 50R | Největší | Σ R | Náhoda Ø R |
|---|---|---|---|---|---|---|---|---|
| po +2R trailing | 25 % | −0,22 ± 0,10 | 0,4 % | 0 % | 0 % | +14,0 | −254 | −0,01 |
| cíl 10R | 13 % | −0,40 ± 0,13 | 0 % | 0 % | 0 % | +10,0 | −472 | −0,02 |
| cíl 20R | 12 % | −0,42 ± 0,14 | 1,4 % | 0 % | 0 % | +19,9 | −490 | −0,02 |
| cíl 50R | 12 % | −0,38 ± 0,18 | 1,4 % | 0,3 % | 0 % | +49,9 | −447 | +0,05 |

Se spotovými náklady (0,15 %) ještě hůř (Ø −0,35 až −0,55 R). Obě poloviny období záporné.

Výzva (start 100 USD, zisky se reinvestují, 10 000 náhodných pořadí týchž obchodů): při riziku 2 / 5 / 10 % na pokus
skončil účet pod 10 USD ve **100 %** případů; na 1 000 USD se dostal nejvýš v 0,5 % případů (cíl 50R, 10 % riziko),
na 10 000 USD v 0 %.

## Závěr

❌ **Neprošlo – ztrácí víc než náhoda.** Prudký pohyb v kryptu obvykle pokračuje (momentum), obrat chytaný proti
němu s těsným stopem vychází hůř než náhodný vstup. Velké trefy existují (1 × 50R, 4 × 20R z 1 177), ale jsou tak vzácné,
že ztráty z ostatních pokusů je mnohonásobně převáží. Znásobování malého účtu touto cestou na datech vede
k jeho ztrátě; výzvy typu „100 → 1 000 000“ na sítích ukazují vítěze, ne všechny pokusy.

Nejde o finanční poradenství.
