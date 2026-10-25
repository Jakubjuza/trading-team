# Hledání lepšího nastavení denních strategií (25. 10. 2026)

Předem stanovený postup (`research/experiments/optimize.py`): pro donchian_1d i pullback_1d 72 nastavení
(držení 20/40/60 dní × trailing 2/3/4 ATR × polovina na T1 ano/ne × víkendový filtr ne/ano × filtr paniky ano/ne)
a 5 rozdělení rizika mezi strategie. Měřítko MAR = R za rok / největší propad v R, portfolio s limity desku,
náklady 0,15 %/stranu, 8 mincí, 12/2016–10/2026. Walk-forward: výběr jen z minulosti, test na dalším roce (5 kroků
2020–2025). Posledních 12 měsíců (od 25. 10. 2025) odloženo jako finální test.

## Walk-forward (výsledky mimo vzorek výběru, 10/2020–10/2025)

| | Obchodů | R za rok | Max. propad R | MAR | Ø R/obchod | Σ R |
|---|---|---|---|---|---|---|
| Vybírané nastavení | 227 | 20,0 | 26,1 | 0,77 | +0,44 | +99,8 |
| **Dnešní nastavení** | 399 | 21,7 | 26,1 | **0,83** | +0,27 | **+108,7** |

Po letech (Σ R) vybírané / dnešní: 2020 7,4 / 19,8 · 2021 41,7 / 33,6 · 2022 11,3 / 19,0 · 2023 28,6 / 9,9 ·
2024 11,9 / 20,3 · 2025 −1,1 / 6,0.

Vybíráno v krocích: Donchian vždy **bez poloviny na T1, držení 60 dní, trailing 3–4 ATR, bez víkendových vstupů**;
pullback nestabilní (držení 20–60, váha 1 → 0,5 → 0).

## Kandidát (výběr na všech datech před testem) a odložený test

Kandidát: jen Donchian (pullback váha 0), držení 60 dní, trailing 4 ATR, celá pozice bez T1, bez víkendových vstupů,
filtr paniky zapnutý.

| | In-sample MAR | In-sample Σ R | Odložený test: obchodů | Σ R | Max. propad R |
|---|---|---|---|---|---|
| Kandidát | 2,71 | +174 | 17 | +2,8 | 4,6 |
| Dnešní | 0,98 | +225 | 70 | +2,4 | 14,3 |

Rozdíl na odloženém testu +0,4 R (90% interval −32 až +32 R) – žádný průkazný rozdíl.
Sousední nastavení kandidáta drží MAR 1,9–2,5 (in-sample) – tvar je robustní, ale in-sample.

## Závěr

- ❌ **Nenavrhuje se.** Postup výběru ve walk-forwardu dnešní nastavení neporazil (MAR 0,77 vs. 0,83, Σ R −9 R)
  a na odloženém roce je rozdíl nulový. Skvělé in-sample číslo kandidáta (MAR 2,7) je typický příklad přeladění.
- Konzistentní vzorec napříč kroky: u Donchianu vyhrávalo **držet celou pozici déle (bez T1, 60 dní, trailing 4 ATR)**
  a nevstupovat o víkendu. Je to jen hypotéza (H6) – rozhodnout na nových datech.
- Dnešní nastavení zůstává; jeho výhoda v posledním roce je malá (+2,4 R za rok, Ø +0,03 R/obchod).

Nejde o finanční poradenství.
