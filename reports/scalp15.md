# Průraz ve směru pohybu na 15M, těsný stop a posouvání stopu + páka a riziko 1–10 % (26. 10. 2026)

Předem stanovený test (`research/experiments/scalp15.py`, běh v GitHub Actions, 15M svíčky OKX, 8 mincí, 10/2024–10/2026).
Navazuje na `reports/reversal.md` (obrat proti pohybu prohrál) – tady se jde **s pohybem**.
Spouštěč: 15M close nad max. 20 svíček (short pod min.), objem ≥ 1,5 × průměr, 1H trend (close vs EMA50);
F1 navíc denní směr (close vs EMA50 1D). Stop za swing 6 svíček − 0,1 ATR, 0,3–1,5 %. Jedna pozice na minci, max. 2 dny.

**10 280 spouštěčů** (5 027 long, 5 253 short). Stop od vstupu: medián 1,0 % (10.–90. percentil 0,55–1,40 %).
Potřebná páka při riziku 1 % účtu: medián 1,0×, 90. percentil 1,8×. Při izolované páce 50× je likvidace ≈ 1,5 % od vstupu.

| Výstup (náklady 0,07 %/stranu) | F0 obchodů | F0 Ø R ± CI | F0 OOS | F1 obchodů | F1 Ø R ± CI | F1 1. / 2. polovina | F1 OOS | Náhoda (F1) |
|---|---|---|---|---|---|---|---|---|
| po +1R na vstup + trailing 2 ATR | 5 546 | −0,12 ± 0,03 | −0,12 | 3 019 | −0,09 ± 0,05 | −0,16 / −0,02 | −0,06 | −0,12 |
| schody (každé +1R posune stop o 1R) | 5 191 | −0,09 ± 0,04 | −0,11 | 2 830 | −0,07 ± 0,06 | −0,14 / −0,00 | −0,05 | −0,12 |
| chandelier 3 ATR | 5 616 | −0,11 ± 0,04 | −0,12 | 3 004 | −0,10 ± 0,05 | −0,18 / −0,01 | −0,05 | −0,13 |
| pevný cíl 2R | 5 066 | −0,10 ± 0,04 | −0,13 | 2 807 | −0,10 ± 0,05 | −0,16 / −0,04 | −0,12 | −0,12 |

S náklady 0,10 % ještě hůř (Ø −0,14 až −0,19 R). Úspěšnost 27–42 %, Ø držení 5–7 h. Záporné na všech 8 mincích.

## Účet 1 000 USD (náklady 0,07 %, jedna pozice naráz, 935–1 659 obchodů za 2 roky)

| Riziko / obchod | Nejlepší varianta (F1 schody) – konec | Max. propad | Nejhorší varianta (F0 BE+trail) – konec | Max. propad |
|---|---|---|---|---|
| 1 % | 421 USD | 60 % | 103 USD | 91 % |
| 2 % | 145 USD | 87 % | 8 USD | 99 % |
| **5 %** | **2 USD** | **100 %** | **0 USD** | **100 %** |
| **10 %** | **0 USD** | **100 %** | **0 USD** | **100 %** |

V 10 000 náhodných pořadích týchž obchodů spadl účet o ≥ 50 % ve 100 % případů u všech variant a všech rizik.

## Závěr

❌ **Neprošlo – všech 8 variant ztrácí.** Jít s pohybem je o 0,02–0,05 R lepší než náhodný vstup (obrat proti pohybu
byl horší než náhoda), ale po nákladech je každá varianta záporná. Posouvání stopu ztrátu zmenšuje (schody −0,07 R vs.
pevný cíl −0,10 R), výhodu nevytvoří. Na 15M náklady (0,07 % × 2 ≈ 0,14 % při stopu 1 %) sežerou zhruba 0,14 R
z každého obchodu – víc, než je hrubá výhoda vstupu. **Riziko 5–10 % na obchod vedlo k nule ve všech variantách.**
Vysoká páka sama nic nemění: rozhoduje riziko na obchod a výhoda po nákladech.

Nejde o finanční poradenství.
