# „Chycení kapitulace“ – long na dně po panice (25. 10. 2026)

Předem stanovený test (`research/experiments/capitulation.py`, běh v GitHub Actions – Fear & Greed z alternative.me).
Signál na denní svíčce: cena ≥ 30 % pod 60denním maximem + volatilita v horních 10 % roku + Fear & Greed < 20
(posledních 3 dní) + svíčka propíchne 20denní minimum a zavře zpět nad ním. Vstup na zavření, stop pod knotem
(min. 1,5 %), celá pozice, po +2R stop na vstup, pak trailing 3 ATR, max. 60 dní. 8 mincí, 2018–2026, náklady 0,15 %.

| Varianta | Obchodů | Úspěšnost | Ø R ± CI | Medián | Σ R | ≥ 5R | Největší | Náhodné vstupy Ø R |
|---|---|---|---|---|---|---|---|---|
| Kapitulace (s Fear & Greed) | 30 | 30 % | +0,30 ± 0,83 | −1,0 | +9,0 | 7 % | +8,6 | **+0,34** |
| Bez Fear & Greed | 57 | 23 % | +0,06 ± 0,59 | −1,0 | +3,1 | 5 % | +10,1 | **+0,84** |

- Obchody přicházejí ve shlucích při velkých krachech (13. 3. 2020: 5 mincí naráz, 5/2022–6/2022: 8 obchodů) –
  fakticky je to pár sázek za 8 let, ne 30 nezávislých obchodů.
- Celý zisk varianty s Fear & Greed dělají 2 obchody z 18. 6. 2022 (AVAX +8,6 R, DOGE +6,9 R); 3 nejlepší = 204 % celku.
  Po letech: 2018 −1,0 · 2019 −3,1 · 2020 +6,8 · 2021 −1,2 · 2022 +9,2 · 2025 −0,4 · 2026 −1,3 R.
- Stop není malý: medián 11 % od vstupu (rozsah 2,6–40 %) – svíčky paniky mají dlouhé knoty.

## Závěr

❌ **Neprošlo.** Výsledek není lepší než náhodný long se stejným stopem a výstupem (+0,30 vs. +0,34 R; bez Fear & Greed
dokonce +0,06 vs. +0,84) a interval spolehlivosti je široký (± 0,83 R). Z denních dat nejde dno spolehlivě
načasovat: většina „kapitulací“ pokračovala dál dolů (70 % obchodů na stopu) a zisk závisí na 1–2 událostech.
Kapitulace zůstávají kontextem pro desk (sentiment-analyst, derivatives-analyst), ne samostatným signálem.

Nejde o finanční poradenství.
