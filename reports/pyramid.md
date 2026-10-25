# Přikupování do vydělávající pozice (pyramiding) na denních signálech (25. 10. 2026)

Předem stanovený test (`research/experiments/pyramid.py`), stejné signály jako dnes (donchian_1d + pullback_1d s filtrem
paniky), 8 mincí, 12/2016–10/2026, náklady 0,15 % na stranu u každého kusu, portfolio s limity desku.
Odložený rok od 25. 10. 2025. 1 R = riziko dnešní plné pozice.

- **P0 dnes:** polovina na T1, zbytek trailing 3 ATR, max. 20 dní.
- **P1:** start 1 kus = 0,5 R; za každý pohyb +1 ATR přidat kus (max. 4); po přidání stop všech kusů = cena přidání − 2 ATR;
  trailing 3 ATR od nejlepšího zavření; max. 60 dní.
- **P2:** jako P1, max. 20 dní.  **P3:** bez přikupování, celá pozice, trailing 3 ATR, max. 60 dní.

| Varianta | Obchodů | Ø R ± CI | R/rok | Max. propad R | MAR | Úspěšnost | ≥ 10R | Max R | IS Ø R | OOS Ø R | Odložený rok Σ R |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P0 dnes | 694 | +0,33 ± 0,13 | 22,9 | 25,8 | 0,89 | 46 % | 0 % | +9,1 | +0,42 | +0,16 | **+2,4** |
| P1 přikup. + 60 dní | 612 | +0,88 ± 0,34 | 54,6 | 34,9 | 1,56 | 25 % | 3,8 % | +44,5 | +1,24 | −0,08 | +17,5 |
| **P2 přikup., 20 dní** | 748 | **+0,70 ± 0,25** | **53,0** | **26,0** | **2,04** | 28 % | 2,9 % | +29,8 | +0,88 | **+0,22** | **+28,7** |
| P3 bez přikup., 60 dní | 551 | +0,57 ± 0,23 | 31,6 | 33,8 | 0,93 | 41 % | 1,8 % | +22,9 | +0,79 | +0,04 | +5,4 |

Párově na stejných 2 936 signálech: P2 − P0 = **+0,38 ± 0,11 R/signál**, v odloženém roce +0,13 R.
Poloviny období (Ø R/obchod): P0 +0,61 / +0,16 · P2 +1,26 / +0,32. Po letech P2 ≥ P0 v 9 z 11 let (2022 a 2025 o 0,4–1,4 R níž).

Robustnost P2 (sousední nastavení, vždy MAR / odložený rok Σ R): rozestup 0,5 / 1,5 ATR → 1,91 / 46,8 · 2,42 / 23,1;
max. 3 / 5 kusů → 1,90 / 22,1 · 2,26 / 31,9; stop po přidání 1,5 / 2,5 ATR → 2,36 / 27,8 · 1,81 / 39,3;
kus 0,33 R → 2,06 / 20,0. Všechna sousední nastavení lépe než P0 (MAR 0,89, +2,4 R).

## Závěr

✅ **P2 prošla kritérii** (OOS lepší o +0,06 R/obchod a v odloženém roce +26 R, obě poloviny, sousední nastavení, stejný
max. propad). P1 (60 dní) a P3 (jen delší držení) v OOS neobstály – přínos dělá přikupování, ne delší držení.

Rizika a omezení: větší pozice (až 4 × 0,5 R = 2× dnešní pozice v ceně) → víc vázaného kapitálu / páka; ztráta jednoho
obchodu může přesáhnout 1 R (nejhorší −1,83 R, když je původní stop těsnější než 2 ATR); úspěšnost klesne na ~28 %
(víc malých ztrát, zisk dělají velké obchody); přidávací příkazy v rychlém trhu dostanou horší cenu (v testu přesně na
úrovni + náklady); zisk soustředěný v býčích letech (2020: +149 R). Zapnutí jen po souhlasu uživatele.

Nejde o finanční poradenství.
