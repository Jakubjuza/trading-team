# Portfolio stylů – poziční (1W) a intradenní swing (4H) (25. 10. 2026)

Otázka: přidat další styly obchodování vedle denních strategií, aby se výsledky doplňovaly?
Metoda (stanovená předem, nic se neladilo): dva setupy, které na denním grafu obstály (Donchian breakout a pullback),
přenesené beze změny pravidel na jiný timeframe. 8 mincí, náklady 0,15 % na stranu, polovina pozice na T1, zbytek
trailing 3 ATR, max. 20 svíček. IS/OOS = prvních 70 % / posledních 30 % obchodů podle času. Náhodné vstupy = stejná
mince, směr, vzdálenost stopu v ATR a cíle v R (20 opakování). Skript: `research/experiments/styles.py`.

- **Poziční (týdenní svíčky, 2016–2026):** kanál 20 týdnů / pullback k EMA 10–20–40 týdnů, trend EMA 40 týdnů (≈ 200 dní).
- **Intradenní swing (4H, 11/2024–10/2026):** stejné parametry jako živé `donchian_1d` a `pullback_1d`, vč. filtru paniky.
- Pro srovnání denní strategie (bez limitů portfolia) – celé období i jen období 4H dat.

| Styl | Obchodů | Za měsíc | Ø R ± CI | IS Ø R | OOS n | OOS Ø R ± CI | Náhoda Ø R | Max. propad R |
|---|---|---|---|---|---|---|---|---|
| Poziční Donchian (1W) | 218 | 1,9 | +0,21 ± 0,22 | +0,35 | 66 | **−0,11 ± 0,29** | +0,01 | 20 |
| Poziční pullback (1W) | 564 | 5,2 | +0,41 ± 0,16 | +0,70 | 170 | **−0,29 ± 0,17** | +0,03 | 56 |
| Swing Donchian (4H) | 1 602 | 67,5 | +0,08 ± 0,07 | +0,18 | 482 | **−0,16 ± 0,14** | −0,04 | 212 |
| Swing pullback (4H) | 2 594 | 113,8 | +0,00 ± 0,06 | +0,06 | 783 | **−0,13 ± 0,10** | −0,03 | 173 |
| *Denní Donchian (živý)* | 1 156 | 9,8 | +0,38 ± 0,09 | +0,45 | 347 | **+0,24 ± 0,15** | +0,11 | 46 |
| *Denní pullback (živý)* | 1 780 | 15,9 | +0,27 ± 0,09 | +0,37 | 534 | **+0,03 ± 0,12** | +0,07 | 102 |

Korelace měsíčních výsledků s denními strategiemi: poziční +0,30 / +0,34, swing 4H +0,24 / +0,44 – nové styly
**nediverzifikují**, vydělávají a ztrácejí ve stejných měsících jako denní strategie.

Po letech (Σ R): poziční pullback 2021 +141, ale 2023 −30, 2025 −42; swing 4H 2024–2025 v plusu, 2026 −80 / −89.

## Závěr

- ❌ **Ani jeden nový styl neprošel.** Všechny čtyři mají OOS po nákladech záporné, pod úrovní náhodných vstupů, a výhoda
  z in-sample (hlavně poziční pullback +0,70 R) v posledních letech zmizela.
- 4H swing generuje 70–110 obchodů měsíčně a náklady 0,15 % na stranu sežerou jeho malou hranu (Ø +0,08 / 0,00 R
  ještě před OOS propadem). Scalping na ještě nižším timeframu by na tom byl s náklady hůř.
- Vedlejší pozorování (NEsloužilo k rozhodnutí, bylo by to dolaďování na stejných datech): 4H Donchian jen long
  Ø +0,24 R, shorty −0,10 R. Případný „4H long-only“ by musel projít novým předem stanoveným testem na jiných datech.
- Rozdíl mezi denními strategiemi a ostatními timeframy odpovídá i dřívějšímu výsledku hodinové strategie
  (brh_1h OOS +0,01 R, vypnutá) – na krypto datech s těmito náklady zatím funguje jen denní graf.
- Diverzifikaci dál zajišťuje **carry z fundingu** (tržně neutrální, v roce 2026 v plusu – reports/carry.md), ne další
  trendový styl. Nic se nezapíná, skener beze změny.

Nejde o finanční poradenství.
