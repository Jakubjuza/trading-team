# Stejné denní strategie na jiných trzích (25. 10. 2026)

donchian_1d + pullback_1d s parametry ze scanner/config.yaml beze změny, denní svíčky yfinance (~10–14 let),
8 instrumentů na trh, stejné výstupy jako živě. Skript: `research/experiments/markets.py`.
Náklady: krypto 0,15 %, měny 0,02 %, akcie 0,05 % na stranu (+ srovnání všech se stejnými 0,15 %).
Náhoda = náhodné vstupy se stejným stopem v ATR a cíli v R. Portfolio = limity desku (max. 2 na strategii a směr,
max. 3 nové za den).

| Trh | Obchodů | Ø R ± CI | IS | OOS ± CI | Náhoda | Od 2022 | Portfolio R/rok | Max. propad R |
|---|---|---|---|---|---|---|---|---|
| Krypto (0,15 %) | 2 936 | +0,315 ± 0,06 | +0,42 | +0,06 ± 0,09 | +0,08 | +0,15 | 25,6 | 24 |
| Měny (0,02 %) | 2 152 | −0,047 ± 0,05 | +0,04 | −0,24 ± 0,07 | −0,01 | −0,23 | −4,2 | 94 |
| Měny (0,15 %) | 2 152 | −0,207 ± 0,05 | −0,13 | −0,40 ± 0,07 | −0,16 | −0,39 | −14,2 | 208 |
| Tech akcie (0,05 %) | 4 047 | +0,271 ± 0,05 | +0,27 | +0,27 ± 0,08 | **+0,22** | +0,24 | 15,0 | 23 |
| Tech akcie (0,15 %) | 4 047 | +0,221 ± 0,04 | +0,22 | +0,22 ± 0,08 | +0,17 | +0,20 | 12,1 | 26 |

Krypto: Donchian +0,38, pullback +0,27 R. Akcie: Donchian +0,23, pullback +0,31 R. Měny: Donchian −0,01, pullback −0,08 R.

## Závěr

- **Měny ❌** – strategie na hlavních měnových párech nefunguje (OOS −0,24 R, pod náhodou, ztrátové roky 2016–2019
  a 2021–2026). Měny se pohybují v menších trendech a víc se vracejí k průměru.
- **Tech akcie – stabilnější, ale výhoda strategie je malá.** Ø +0,27 R a OOS stejné (+0,27), ALE náhodné vstupy
  dávají +0,22 R: vybraných 8 akcií (dnešní vítězové AAPL, MSFT, NVDA…) za 10 let mnohonásobně vyrostlo, takže vydělává
  skoro každý long (survivorship bias). Vlastní přínos strategie nad náhodou je ~+0,05 R, u krypta ~+0,23 R.
- **Krypto ✅ má největší výhodu strategie** (nad náhodou) i nejvíc R za rok v portfoliu (25,6 vs. 15,0), ale slábne
  (od 2022 +0,15 R, rok 2026 zatím ~0).
- Férový test akcií by potřeboval index nebo širší koš bez výběru vítězů (např. sektorová ETF) – neprovedeno.

Nejde o finanční poradenství.
