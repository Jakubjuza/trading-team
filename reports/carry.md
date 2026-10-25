# Carry z fundingu – backtest (2026-10-25)

Hyperliquid (historie fundingu dostupná od 3. 11. 2024, tj. ~1 rok), pravidlo vstup > 10 % p.a. / výstup < 0 %
(7denní průměr), náklady 0,49 % velikosti pozice za celý obchod (4 obchody), kapitál 1,5× pozice (perp s pákou 2×).
Spuštěno v GitHub Actions (workflow „Výzkum naživo“, `python3 research/carry.py --report`).

| Mince | Výnos p.a. na kapitál | Pořád v pozici | Max. propad | V pozici | Obchodů | Nejhorší měsíc | Ø funding p.a. | Hodin se záporným fundingem | 2024 / 2025 / 2026 |
|---|---|---|---|---|---|---|---|---|---|
| BTC | +5,78 % | +6,66 % | 0,38 % | 73 % | 3 | −0,06 % | +10,1 % | 13 % | +3,14 / +6,54 / +1,74 % |
| ETH | +4,77 % | +6,33 % | 0,40 % | 68 % | 6 | −0,25 % | +9,6 % | 16 % | +3,58 / +3,93 / +1,91 % |
| SOL | +3,38 % | +3,85 % | 1,06 % | 49 % | 7 | −0,35 % | +6,0 % | 27 % | +3,78 / +2,43 / +0,46 % |
| XRP | +5,34 % | +5,24 % | 0,44 % | 59 % | 4 | −0,21 % | +8,0 % | 22 % | +3,41 / +5,95 / +1,20 % |
| DOGE | +5,36 % | +7,10 % | 0,49 % | 68 % | 8 | −0,30 % | +10,9 % | 18 % | +4,55 / +4,30 / +1,73 % |
| AVAX | +3,52 % | +4,94 % | 0,84 % | 53 % | 8 | −0,18 % | +7,5 % | 23 % | +3,25 / +2,60 / +1,10 % |
| LINK | +8,52 % | +8,75 % | 0,31 % | 98 % | 2 | −0,11 % | +13,2 % | 6 % | +4,10 / +7,46 / +5,26 % |
| ADA | +2,00 % | +1,56 % | 1,22 % | 38 % | 5 | −0,34 % | +2,5 % | 33 % | +1,56 / +3,39 / −1,00 % |

(2024 = jen listopad–prosinec.)

Čtení:
- Skromný, ale stabilní výnos (2–8,5 % p.a. na kapitál) s propady do ~1 % – vydělával i v roce 2026, kdy trendové
  strategie ztrácejí. Je to jiný zdroj výnosu než trend (platí ho páka ostatních, ne pohyb ceny).
- Pravidlo vstupu > 10 % p.a. přidalo málo – „pořád v pozici“ vyšlo často o něco lépe. Vzorek ~1 rok.
- Rizika mimo backtest: likvidace short perpu při prudkém růstu bez doplnění marže, riziko burzy / smart contractu,
  kolísání rozdílu cen spot × perp. Vyžaduje futures účet → **jen papírově** (skener: `carry` v config.yaml).

Nejde o finanční poradenství.
