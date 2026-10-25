# Vstup z nižších timeframů pro denní signály (25. 10. 2026)

Signál a směr z denního grafu (donchian_1d, pullback_1d, s filtrem paniky), vstup hledaný na nižších TF.
725 denních signálů 11/2024–10/2026, 8 mincí, hodinová data, náklady 0,15 % na stranu, stejné výstupy pro všechny
varianty (50 % na T1, zbytek trailing 3 denní ATR, max. 20 dní). Varianty stanovené předem.
Skript: `research/experiments/mtf_entry.py`, logika vstupu: `scanner/mtf.py` (stejná ve skeneru i v testu).

| Vstup | Otevřeno | Ø R na obchod | Ø R na signál |
|---|---|---|---|
| A zavření denní svíčky | 100 % | +0,083 ± 0,10 | +0,083 |
| B limit o 0,5 denního ATR lépe | 62 % | −0,075 ± 0,15 | −0,047 |
| **C 4H ve směru + 1H návrat k EMA20 + 1H obratová svíčka, stop za swingem 6 svíček** | 95 % | +0,134 ± 0,25 | **+0,126** |
| D jako C, ale původní denní stop | 95 % | +0,020 ± 0,10 | +0,019 |

- Zlepšení C dělá hlavně **těsnější stop** (D = jen lepší načasování nepomohlo).
- C vynechalo 39 signálů, které by při vstupu na zavření dopadly Ø −0,59 R.
- Pullback: C +0,104 vs. A +0,015 R. Donchian: A +0,241 vs. C +0,178 R (silné průrazy nečekají).
- Zatím **není statisticky průkazné** (interval ±0,25 R), 1. polovina období lépe A, 2. polovina C, po mincích smíšeně.
- 15M: historie zdarma jen ~60 dní → netestovatelné; ve skeneru zatím 1H spouštěč.

Rozhodnutí: skener u každého denního signálu hledá vstup C a vede ho **papírově souběžně** s denní variantou
(strategie „…+mtf“ v research/outcomes.jsonl). Po ~30 signálech se rozhodne podle živých výsledků.

Nejde o finanční poradenství.
