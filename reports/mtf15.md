# Vstup z nižších TF: sweep & reclaim na 1H (H4) a spouštěč na 15M (25. 10. 2026)

Předem stanovený test, nic se neladilo (`research/experiments/mtf15.py`, běh v GitHub Actions – 15M data z OKX).
728 denních signálů (donchian_1d + pullback_1d s filtrem paniky), 8 mincí, 11/2024–09/2026. Všechny varianty
vyhodnocené na stejných 15M svíčkách, cíle z denního signálu, polovina na T1, zbytek trailing 3 denní ATR, max. 20 dní,
náklady 0,15 % na stranu. Nesplněný spouštěč do 72 h = 0 R. OOS = posledních 30 % signálů (od 22. 3. 2026).

| Varianta | Otevřeno | Ø R / obchod ± CI | Ø R / signál | IS | OOS ± CI |
|---|---|---|---|---|---|
| A zavření denní svíčky | 100 % | +0,072 ± 0,10 | +0,072 | +0,162 | −0,132 ± 0,17 |
| **C dnes: 4H → 1H spouštěč** | 95 % | +0,072 ± 0,24 | +0,068 | +0,044 | **+0,124 ± 0,46** |
| H4 sweep & reclaim 1H | 97 % | +0,040 ± 0,28 | +0,039 | −0,064 | +0,273 ± 0,49 |
| M15 1H → 15M spouštěč | 98 % | +0,351 ± 0,29 | +0,345 | +0,562 | **−0,148 ± 0,38** |

Párově proti C (Ø rozdíl R/signál, celé období): A +0,004 ± 0,20 · H4 −0,029 ± 0,19 · **M15 +0,276 ± 0,25**.
Poloviny období (Ø R/signál): C −0,03 / +0,17 · H4 −0,04 / +0,11 · M15 +0,40 / +0,29.
Strategie: pullback C +0,01 vs. M15 +0,33; Donchian C +0,19 vs. M15 +0,39.
Mince M15 − C: lepší na BTC, ETH, SOL, XRP, LINK, DOGE; horší na ADA, AVAX. Velkou část náskoku dělá ETH (+1,47 vs. +0,20).

## Závěr

- ❌ **H4 sweep & reclaim na 1H neprošel** – oproti dnešnímu vstupu −0,03 R/signál, in-sample záporný. Postup z videa
  na denních signálech kryptoměn výhodu nepřidal.
- 🧪 **M15 je nerozhodnutý** – za celé období výrazně lepší než dnešní 1H vstup (+0,28 ± 0,25 R/signál, kladný v obou
  polovinách a na 6 z 8 mincí), ale v posledních 30 % (OOS) horší (−0,15 vs. +0,12). Podle pravidel (OOS zlepšení
  ≥ 0,05 R) **neprošel**, takže se nic nemění. Rozdíl je zatím zatížený velkým rozptylem a jednou mincí (ETH).
- Dnešní vstup C zůstává. Rozumný další krok: sledovat M15 papírově souběžně (jako dnes C) a rozhodnout na nových,
  neviděných datech.

Nejde o finanční poradenství.
