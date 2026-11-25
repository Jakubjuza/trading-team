# Downtown – divoké strategie (jen papír)

Aktualizováno 2026-11-25 14:14 UTC skriptem `research/downtown.py` (pravidla stanovená předem v hlavičce).
Oddělené od desku: na skener, registr, riziko ani peníze nesahá. Každá strategie má papírový účet 1 000 USDT,
páku, reinvestici a skutečnou likvidaci; po bankrotu se vloží nových 1 000 USDT. Nejde o finanční poradenství.

## Zpětný test od 2023-01-01 (Kronos ×10 až od 1. 9. 2025)

| Strategie | Páka | Vloženo | Účet teď | Max. účet | Čistě | Max propad | Likvidace | Bankroty | Obchodů | Výher | Nejlepší měsíc | Nejhorší měsíc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Scalper 15m ×20 | 20× | 191 000 | 322 | 1 677 | -190 678 (-99.8 %) | -93.8 % | 0 | 190 | 13666 | 38.8 % | -78.2 % | -97.9 % |
| Průraz ×25 | 25× | 139 000 | 10 855 | 37 939 | -128 145 (-92.2 %) | -99.6 % | 10 | 138 | 2465 | 24.6 % | 820.4 % | -98.7 % |
| Knock-out ×50 | 50× | 227 000 | 311 | 71 135 | -226 689 (-99.9 %) | -99.8 % | 0 | 226 | 2011 | 22.9 % | -23.6 % | -98.1 % |
| Martingale ×10 | 10× | 1 000 | 214 | 1 013 | -786 (-78.6 %) | -80.3 % | 0 | 0 | 1754 | 46.2 % | 1.9 % | -23.8 % |
| Lovec propadů ×15 | 15× | 12 000 | 984 | 3 249 | -11 016 (-91.8 %) | -96.8 % | 2 | 11 | 277 | 42.2 % | 73.1 % | -83.9 % |
| Rotace hybnosti ×5 | 5× | 13 000 | 227 | 314 458 | -12 773 (-98.3 %) | -99.8 % | 1 | 12 | 2522 | 40.7 % | 3991.9 % | -99.7 % |
| Kronos ×10 | 10× | 30 000 | 625 | 1 626 | -29 375 (-97.9 %) | -93.1 % | 2 | 29 | 4340 | 43.1 % | -68.1 % | -96.1 % |
| Týdenní hybnost ×3 | 3× | 3 000 | 292 | 14 270 | -2 708 (-90.3 %) | -98.7 % | 1 | 2 | 224 | 45.5 % | 848.9 % | -94.6 % |
| Squeeze průraz ×10 | 10× | 10 000 | 986 | 13 899 | -9 014 (-90.1 %) | -99.3 % | 0 | 9 | 867 | 28.1 % | 362.2 % | -84.6 % |
| BTC ×3, jen drž | 3× | 1 000 | 7 345 | 19 821 | 6 345 (634.5 %) | -64.7 % | 0 | 0 | 0 | – | 116.3 % | -31.9 % |

Roky (čistá křivka, % za rok):

- **Scalper 15m ×20**: 2023: -97.7 %, 2024: -99.3 %, 2025: -99.4 %, 2026: -99.2 %
- **Průraz ×25**: 2023: -97.7 %, 2024: -99.8 %, 2025: -95.1 %, 2026: -54.4 %
- **Knock-out ×50**: 2023: -99.2 %, 2024: -98.6 %, 2025: -99.7 %, 2026: -99.0 %
- **Martingale ×10**: 2023: -19.8 %, 2024: -40.9 %, 2025: -21.0 %, 2026: -42.8 %
- **Lovec propadů ×15**: 2023: -80.8 %, 2024: -87.9 %, 2025: -96.3 %, 2026: -68.5 %
- **Rotace hybnosti ×5**: 2023: 2391.3 %, 2024: -89.7 %, 2025: -98.6 %, 2026: -94.6 %
- **Kronos ×10**: 2025: -97.3 %, 2026: -96.9 %
- **Týdenní hybnost ×3**: 2023: 270.2 %, 2024: -7.2 %, 2025: -79.8 %, 2026: -73.4 %
- **Squeeze průraz ×10**: 2023: -91.4 %, 2024: -91.7 %, 2025: -59.9 %, 2026: -69.9 %
- **BTC ×3, jen drž**: 2023: 433.4 %, 2024: 168.2 %, 2025: -9.8 %, 2026: -43.0 %

## Živý papír od 2026-11-07

| Strategie | Účet | Čistě | Obchodů | Likvidace | Otevřená pozice |
|---|---:|---:|---:|---:|---|
| Scalper 15m ×20 | 422 | -2 578 | 198 | 0 | – |
| Průraz ×25 | 2 212 | 1 212 | 19 | 0 | BTC short od 2026-11-24T03:00 |
| Knock-out ×50 | 165 | -1 835 | 7 | 0 | – |
| Martingale ×10 | 959 | -41 | 62 | 0 | – |
| Lovec propadů ×15 | 965 | -35 | 3 | 0 | – |
| Rotace hybnosti ×5 | 192 | -808 | 31 | 0 | – |
| Kronos ×10 | 162 | -838 | 211 | 0 | – |
| Týdenní hybnost ×3 | 1 000 | 0 | 0 | 0 | – |
| Squeeze průraz ×10 | 937 | -63 | 10 | 0 | XRP short od 2026-11-25T12:00 |
| BTC ×3, jen drž | 301 | -699 | 0 | 0 | BTC long od 2026-11-07T00:00 |

## Dispečer fází

Agent, který strategie nasazuje jen ve fázích trhu, kde dřív vydělávaly: [reports/downtown_dispatch.md](downtown_dispatch.md), výzkum v [reports/downtown_regimes.md](downtown_regimes.md).
