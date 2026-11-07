# Downtown – Dispečer fází (jen papír)

Aktualizováno 2026-11-07T19:32+00:00 UTC skriptem `research/downtown_dispatch.py` (pravidla stanovená předem v hlavičce).
Agent nasazuje divoké strategie Downtownu jen ve fázích trhu, kde dřív vydělávaly; výzkum v `reports/downtown_regimes.md`.
Oddělené od desku, nejde o finanční poradenství.

## Teď

- **Fáze trhu:** býk · pila · klid (data k 2026-11-06: BTC 75 848 vs. 200denní průměr 73 242  efektivita 30 dní 0.23 (trend ≥ 0.25)  volatilita 36 % vs. medián 40 %)
- **Nasazeno:** nic – hotovost (v této fázi žádná strategie neprošla)
- **Plán tohoto měsíce:** býk · trend · divoko → Týdenní hybnost ×3, Rotace hybnosti ×5

## Zpětný test od 2023-07-01 (walk-forward, učení jen z minulých obchodů)

Vloženo 1 000 → hodnota 836 USDT (z toho trezor 0)  čistě -164 USDT; max. hodnota 1 833; max. propad -82.4 %; bankroty 0; obchodů 50.

Roky: 2023: 0.0 %, 2024: -53.5 %, 2025: 39.4 %, 2026: 29.2 %

## Živý papír od 2026-11-08

Účet 1 000 USDT  čistě 0  obchodů 0.

## Kde která strategie vydělávala (bez páky, průměr na obchod, všechny dosavadní obchody)

| Strategie | býk · pila · divoko | býk · pila · klid | býk · trend · divoko | býk · trend · klid | medvěd · pila · divoko | medvěd · pila · klid | medvěd · trend · divoko | medvěd · trend · klid |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Scalper 15m ×20 | -0.15 % (n 2343, t -21.5) | -0.15 % (n 3060, t -25.3) | -0.17 % (n 1522, t -20.0) | -0.17 % (n 1381, t -18.8) | -0.16 % (n 1581, t -18.6) | -0.14 % (n 1119, t -14.8) | -0.13 % (n 913, t -11.8) | -0.16 % (n 548, t -11.6) |
| Průraz ×25 | -0.14 % (n 380, t -1.3) | -0.12 % (n 590, t -1.2) | -0.21 % (n 276, t -1.2) | -0.17 % (n 274, t -1.4) | -0.09 % (n 251, t -0.6) | -0.15 % (n 260, t -1.6) | -0.08 % (n 117, t -0.3) | -0.11 % (n 111, t -0.6) |
| Knock-out ×50 | -0.20 % (n 333, t -2.5) | -0.13 % (n 396, t -1.7) | -0.20 % (n 365, t -2.7) | +0.02 % (n 250, t +0.2) | -0.07 % (n 175, t -0.6) | -0.15 % (n 158, t -1.4) | -0.04 % (n 75, t -0.2) | -0.17 % (n 58, t -0.9) |
| Martingale ×10 | -0.17 % (n 300, t -3.1) | -0.19 % (n 361, t -3.8) | -0.22 % (n 153, t -2.8) | -0.22 % (n 155, t -2.9) | -0.17 % (n 214, t -2.5) | -0.28 % (n 145, t -3.5) | -0.21 % (n 156, t -2.7) | -0.35 % (n 98, t -3.6) |
| Lovec propadů ×15 | -0.21 % (n 39, t -0.8) | -0.47 % (n 72, t -2.0) | -0.25 % (n 18, t -0.4) | -0.55 % (n 23, t -1.7) | -0.73 % (n 33, t -2.5) | -0.28 % (n 37, t -1.6) | -0.31 % (n 14, t -1.0) | -0.48 % (n 12, t -1.2) |
| Rotace hybnosti ×5 | -0.10 % (n 404, t -0.7) | -0.04 % (n 580, t -0.3) | **+0.79 % (n 249, t +2.2)** | +0.39 % (n 242, t +1.4) | -0.30 % (n 313, t -2.1) | -0.05 % (n 252, t -0.3) | -0.16 % (n 152, t -0.8) | -0.20 % (n 110, t -0.8) |
| Kronos ×10 | -0.17 % (n 240, t -3.1) | -0.15 % (n 650, t -5.2) | -0.13 % (n 325, t -3.1) | -0.24 % (n 125, t -3.7) | -0.16 % (n 808, t -5.7) | -0.13 % (n 814, t -4.8) | -0.08 % (n 906, t -2.4) | -0.08 % (n 267, t -1.5) |
| Týdenní hybnost ×3 | -2.71 % (n 35, t -1.3) | -0.58 % (n 52, t -0.6) | **+10.96 % (n 21, t +3.2)** | +12.15 % (n 16, t +0.9) | +0.70 % (n 32, t +0.6) | +0.16 % (n 31, t +0.1) | -1.84 % (n 4, t -0.5) | -2.06 % (n 8, t -1.2) |
| Squeeze průraz ×10 | +0.01 % (n 142, t +0.1) | +0.08 % (n 205, t +0.4) | +1.17 % (n 72, t +1.6) | -0.14 % (n 74, t -0.3) | -0.05 % (n 106, t -0.2) | -0.15 % (n 95, t -0.8) | -0.03 % (n 50, t -0.1) | -0.01 % (n 34, t -0.0) |
| BTC ×3, jen drž | +0.09 % (n 227, t +0.6) | -0.07 % (n 336, t -0.7) | +0.13 % (n 140, t +0.6) | +0.45 % (n 136, t +1.9) | +0.20 % (n 163, t +0.9) | +0.02 % (n 147, t +0.1) | +0.06 % (n 88, t +0.2) | -0.41 % (n 62, t -1.6) |

Tučně = fáze splňuje pravidlo (≥ 12 obchodů, průměr > 0, t ≥ 1). Podíl dní ve fázích: býk · pila · klid 26 %, býk · pila · divoko 18 %, medvěd · pila · divoko 12 %, medvěd · pila · klid 11 %, býk · trend · divoko 11 %, býk · trend · klid 10 %, medvěd · trend · divoko 7 %, medvěd · trend · klid 5 %.
