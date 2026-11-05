# 🎯 Vstup na průrazu úrovně vs. zavření denní svíčky – výsledky testu

Spuštěno 2026-11-05 18:46 UTC. Pravidla předem (hlavička `research/experiments/level_entry.py`). donchian_1d, 8 mincí, 1H provedení 2024-11 – 2026-10, náklady 0,15 %/stranu + 0,05 % skluz na úrovni.

| varianta | obchodů | výhry | Ø R ± CI | R/rok | 1. pol. Ø R (n) | 2. pol. Ø R (n) | long Ø R | short Ø R |
|---|---|---|---|---|---|---|---|---|
| A dnes – zavření denní svíčky | 124 | 46 % | +0,176 ± 0.24 | +11 | +0,005 (68) | +0,383 (56) | +0,034 | +0,278 |
| E stop příkaz na úrovni | 167 | 46 % | +0,242 ± 0.22 | +21 | +0,259 (85) | +0,224 (82) | +0,238 | +0,245 |
| E2 + 1H trend ve směru | 166 | 46 % | +0,249 ± 0.22 | +21 | +0,259 (85) | +0,239 (81) | +0,256 | +0,245 |
| E3 + 1H trend, stop za 1H swingem | 232 | 47 % | +0,344 ± 0.25 | +41 | +0,458 (114) | +0,233 (118) | +0,524 | +0,214 |

## Verdikt

- E stop příkaz na úrovni: **NEPROŠLO ❌** – Ø R +0,259 / +0,224 vs. A +0,005 / +0,383; R/rok +23 / +19 vs. A +0 / +22
- E2 + 1H trend ve směru: **NEPROŠLO ❌** – Ø R +0,259 / +0,239 vs. A +0,005 / +0,383; R/rok +23 / +20 vs. A +0 / +22
- E3 + 1H trend, stop za 1H swingem: **NEPROŠLO ❌** – Ø R +0,458 / +0,233 vs. A +0,005 / +0,383; R/rok +54 / +28 vs. A +0 / +22

Po mincích (Ø R):

| mince | A | E | E2 | E3 |
|---|---|---|---|---|
| BTC | +0,215 (14) | +0,346 (18) | +0,346 (18) | +0,555 (27) |
| ETH | +0,580 (15) | +0,434 (20) | +0,512 (19) | +0,620 (26) |
| SOL | +0,188 (18) | +0,385 (20) | +0,386 (20) | +0,172 (35) |
| XRP | +0,038 (17) | +0,173 (25) | +0,173 (25) | +0,265 (34) |
| ADA | -0,258 (18) | -0,066 (21) | -0,066 (21) | +0,105 (28) |
| LINK | +0,306 (14) | +0,533 (17) | +0,533 (17) | +0,734 (24) |
| AVAX | +0,580 (13) | +0,231 (22) | +0,231 (22) | +0,273 (29) |
| DOGE | -0,076 (15) | +0,028 (24) | +0,028 (24) | +0,177 (29) |

Pozn.: u E se stop ve stejné hodině jako vstup nepočítá (hodinová data neříkají pořadí) – to E mírně zvýhodňuje; proto je laťka +0,05 R v obou polovinách.

Rozhodnutí: co PROŠLO, jde papírově souběžně s dnešním vstupem; jinak beze změny. Nejde o finanční poradenství.
