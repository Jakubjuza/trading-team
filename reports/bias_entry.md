# Směr z denního grafu + průběžné vstupy na 1H (26. 10. 2026)

Předem stanovený test (`research/experiments/bias_entry.py`), 8 mincí, 1H svíčky 11/2024–10/2026, náklady 0,15 %/stranu.
A: směr dne (Close vs. EMA200 a sklon EMA50) → vstupy kdykoli na 1H při návratu k EMA20 a obratové svíčce ve směru.
B: stejné 1H vstupy oběma směry bez denního směru. Stop za swingem 6 svíček (min. 1,5 %), 1 pozice na minci.

| Varianta | Obchodů | Za měsíc | Úspěšnost | Ø R ± CI | 1./2. polovina | R/rok | Max. propad R | Náhoda |
|---|---|---|---|---|---|---|---|---|
| A směr + 1H, cíle 2R/4R, 5 dní | 1 748 | 76 | 37 % | −0,04 ± 0,07 | −0,11 / +0,04 | −33 | 181 | −0,07 |
| B oba směry, cíle 2R/4R, 5 dní | 2 139 | 93 | 37 % | −0,05 ± 0,06 | −0,04 / −0,07 | −58 | 162 | −0,06 |
| **A směr + 1H, trailing jako dnes, 20 dní** | 827 | 36 | 35 % | **+0,10 ± 0,16** | +0,04 / +0,18 | **+45** | 77 | −0,05 |
| B oba směry, trailing, 20 dní | 994 | 43 | 35 % | +0,02 ± 0,13 | +0,04 / −0,01 | +10 | 68 | −0,01 |
| Dnes: denní Donchian + pullback | 737 | 32 | 43 % | +0,08 ± 0,10 | 0,00 / +0,13 | +30 | 86 | – |

A s trailingem: long 344 obchodů Ø +0,16 R, short 483 Ø +0,07 R; stop medián 2,7 %.

## Závěr

- **Směr z denního grafu je podstatný**: bez něj (B „oba směry“) je výsledek kolem nuly. Obchodovat oba směry
  podle toho, co trh nabídne na 1H, výhodu nepřidává.
- **Pevné cíle 2R/4R s krátkým držením ztrácejí** (−0,04 R) – zisk dělá nechat obchod běžet (trailing).
- 🧪 **A s trailingem je slibná, ale neprůkazná**: +0,10 ± 0,16 R/obchod, +45 R/rok vs. dnešních +30 R/rok za stejné
  období, nad náhodou (−0,05), lepší v obou polovinách – ale interval spolehlivosti zahrnuje nulu a data jsou jen 2 roky.
  Kritérium (OOS ≥ 0,05 R lepší, ≥ 100 obchodů) splňuje jen těsně ve 2. polovině (+0,18 vs. +0,13). → hypotéza H7,
  vhodná k papírovému ověření naživo, ne k nahrazení dnešních strategií.

Nejde o finanční poradenství.
