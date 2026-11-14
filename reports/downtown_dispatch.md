# Downtown – Dispečer fází (jen papír)

Aktualizováno 2026-11-14T00:52+00:00 UTC skriptem `research/downtown_dispatch.py` (pravidla stanovená předem v hlavičce).
Agent nasazuje divoké strategie Downtownu jen ve fázích trhu, kde dřív vydělávaly; výzkum v `reports/downtown_regimes.md`.
Oddělené od desku, nejde o finanční poradenství.

## Teď

- **Fáze trhu:** medvěd · trend · klid (data k 2026-11-13: BTC 68 311 vs. 200denní průměr 73 092, efektivita 30 dní 0.40 (trend od 0.25), volatilita 38 % vs. medián 40 %)
- **Nasazeno:** nic – hotovost (v této fázi žádná strategie neprošla)
- **Plán tohoto měsíce:** býk · trend · divoko → Týdenní hybnost ×3, Rotace hybnosti ×5, Squeeze průraz ×10; býk · trend · klid → BTC ×3, jen drž, Rotace hybnosti ×5

## Zpětný test od 2023-07-01 (walk-forward, učení jen z minulých obchodů)

Vloženo celkem 2 000 → hodnota 10 146 USDT (z toho trezor 9 620), čistě 8 146 USDT; max. hodnota 12 903; max. propad -61.8 %; bankroty 1; obchodů 374.

Roky: 2023: 345.0 %, 2024: 133.9 %, 2025: -12.3 %, 2026: 1.4 %

## Živý papír od 2026-11-08

Účet 798 USDT, čistě -202, obchodů 1.

## Kde která strategie vydělávala (bez páky, průměr na obchod, všechny dosavadní obchody)

| Strategie | býk · pila · divoko | býk · pila · klid | býk · trend · divoko | býk · trend · klid | medvěd · pila · divoko | medvěd · pila · klid | medvěd · trend · divoko | medvěd · trend · klid |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Scalper 15m ×20 | -0.15 % (n 2343, t -21.5) | -0.15 % (n 3088, t -25.3) | -0.17 % (n 1522, t -20.0) | -0.17 % (n 1394, t -18.7) | -0.16 % (n 1581, t -18.6) | -0.14 % (n 1119, t -14.8) | -0.13 % (n 913, t -11.8) | -0.16 % (n 558, t -11.4) |
| Průraz ×25 | -0.14 % (n 380, t -1.3) | -0.11 % (n 596, t -1.2) | -0.21 % (n 276, t -1.2) | -0.17 % (n 276, t -1.4) | -0.09 % (n 251, t -0.6) | -0.15 % (n 260, t -1.6) | -0.08 % (n 117, t -0.3) | -0.11 % (n 113, t -0.6) |
| Knock-out ×50 | -0.20 % (n 333, t -2.5) | -0.13 % (n 399, t -1.8) | -0.20 % (n 365, t -2.7) | +0.01 % (n 251, t +0.1) | -0.07 % (n 175, t -0.6) | -0.15 % (n 158, t -1.4) | -0.04 % (n 75, t -0.2) | -0.18 % (n 59, t -0.9) |
| Martingale ×10 | -0.17 % (n 300, t -3.1) | -0.19 % (n 368, t -3.8) | -0.22 % (n 153, t -2.8) | -0.24 % (n 158, t -3.1) | -0.17 % (n 214, t -2.5) | -0.28 % (n 145, t -3.5) | -0.21 % (n 156, t -2.7) | -0.35 % (n 106, t -3.7) |
| Lovec propadů ×15 | -0.21 % (n 39, t -0.8) | -0.43 % (n 74, t -1.9) | -0.25 % (n 18, t -0.4) | -0.55 % (n 23, t -1.7) | -0.73 % (n 33, t -2.5) | -0.28 % (n 37, t -1.6) | -0.31 % (n 14, t -1.0) | -0.48 % (n 12, t -1.2) |
| Rotace hybnosti ×5 | -0.10 % (n 404, t -0.7) | -0.06 % (n 584, t -0.5) | **+0.79 % (n 249, t +2.2)** | **+0.39 % (n 243, t +1.4)** | -0.30 % (n 313, t -2.1) | -0.05 % (n 252, t -0.3) | -0.16 % (n 152, t -0.8) | -0.20 % (n 112, t -0.9) |
| Týdenní hybnost ×3 | -2.71 % (n 35, t -1.3) | -0.58 % (n 52, t -0.6) | **+10.96 % (n 21, t +3.2)** | +12.15 % (n 16, t +0.9) | +0.70 % (n 32, t +0.6) | +0.16 % (n 31, t +0.1) | -1.84 % (n 4, t -0.5) | -2.06 % (n 8, t -1.2) |
| Squeeze průraz ×10 | +0.01 % (n 142, t +0.1) | +0.07 % (n 208, t +0.4) | **+1.17 % (n 72, t +1.6)** | -0.14 % (n 74, t -0.3) | -0.05 % (n 106, t -0.2) | -0.15 % (n 95, t -0.8) | -0.03 % (n 50, t -0.1) | -0.01 % (n 34, t -0.0) |
| BTC ×3, jen drž | +0.09 % (n 227, t +0.6) | -0.08 % (n 339, t -0.8) | +0.13 % (n 140, t +0.6) | **+0.42 % (n 138, t +1.8)** | +0.20 % (n 163, t +0.9) | +0.02 % (n 147, t +0.1) | +0.06 % (n 88, t +0.2) | -0.47 % (n 64, t -1.8) |

Tučně = fáze splňuje pravidlo (≥ 12 obchodů, průměr > 0, t ≥ 1). Podíl dní ve fázích: býk · pila · klid 26 %, býk · pila · divoko 17 %, medvěd · pila · divoko 12 %, medvěd · pila · klid 11 %, býk · trend · divoko 11 %, býk · trend · klid 11 %, medvěd · trend · divoko 7 %, medvěd · trend · klid 5 %.
