# Downtown – divoké strategie (jen papír)

Aktualizováno 2026-11-21 01:26 UTC skriptem `research/downtown.py` (pravidla stanovená předem v hlavičce).
Oddělené od desku: na skener, registr, riziko ani peníze nesahá. Každá strategie má papírový účet 1 000 USDT,
páku, reinvestici a skutečnou likvidaci; po bankrotu se vloží nových 1 000 USDT. Nejde o finanční poradenství.

## Zpětný test od 2023-01-01 (Kronos ×10 až od 1. 9. 2025)

| Strategie | Páka | Vloženo | Účet teď | Max. účet | Čistě | Max propad | Likvidace | Bankroty | Obchodů | Výher | Nejlepší měsíc | Nejhorší měsíc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Scalper 15m ×20 | 20× | 190 000 | 636 | 1 677 | -189 364 (-99.7 %) | -93.8 % | 0 | 189 | 13603 | 38.9 % | -73.0 % | -97.9 % |
| Průraz ×25 | 25× | 139 000 | 9 331 | 37 939 | -129 669 (-93.3 %) | -99.6 % | 10 | 138 | 2462 | 24.6 % | 691.2 % | -98.7 % |
| Knock-out ×50 | 50× | 227 000 | 1 088 | 71 135 | -225 912 (-99.5 %) | -99.8 % | 0 | 226 | 2009 | 22.9 % | -23.6 % | -98.1 % |
| Martingale ×10 | 10× | 1 000 | 215 | 1 013 | -785 (-78.5 %) | -80.3 % | 0 | 0 | 1742 | 46.3 % | 1.9 % | -23.8 % |
| Lovec propadů ×15 | 15× | 12 000 | 984 | 3 249 | -11 016 (-91.8 %) | -96.8 % | 2 | 11 | 277 | 42.2 % | 73.1 % | -83.9 % |
| Rotace hybnosti ×5 | 5× | 13 000 | 288 | 314 458 | -12 712 (-97.8 %) | -99.8 % | 1 | 12 | 2511 | 40.7 % | 3991.9 % | -99.7 % |
| Kronos ×10 | 10× | 30 000 | 883 | 1 626 | -29 117 (-97.1 %) | -93.1 % | 2 | 29 | 4286 | 43.1 % | -54.9 % | -96.1 % |
| Týdenní hybnost ×3 | 3× | 3 000 | 292 | 14 270 | -2 708 (-90.3 %) | -98.7 % | 1 | 2 | 224 | 45.5 % | 848.9 % | -94.6 % |
| Squeeze průraz ×10 | 10× | 10 000 | 433 | 13 899 | -9 567 (-95.7 %) | -99.3 % | 0 | 9 | 865 | 28.0 % | 362.2 % | -84.6 % |
| BTC ×3, jen drž | 3× | 1 000 | 7 406 | 19 821 | 6 406 (640.6 %) | -63.0 % | 0 | 0 | 0 | – | 116.3 % | -31.4 % |

Roky (čistá křivka, % za rok):

- **Scalper 15m ×20**: 2023: -97.7 %, 2024: -99.3 %, 2025: -99.4 %, 2026: -98.3 %
- **Průraz ×25**: 2023: -97.7 %, 2024: -99.8 %, 2025: -95.1 %, 2026: -60.8 %
- **Knock-out ×50**: 2023: -99.2 %, 2024: -98.6 %, 2025: -99.7 %, 2026: -96.5 %
- **Martingale ×10**: 2023: -19.8 %, 2024: -40.9 %, 2025: -21.0 %, 2026: -42.4 %
- **Lovec propadů ×15**: 2023: -80.8 %, 2024: -87.9 %, 2025: -96.3 %, 2026: -68.5 %
- **Rotace hybnosti ×5**: 2023: 2391.3 %, 2024: -89.7 %, 2025: -98.6 %, 2026: -93.1 %
- **Kronos ×10**: 2025: -97.3 %, 2026: -95.6 %
- **Týdenní hybnost ×3**: 2023: 270.2 %, 2024: -7.2 %, 2025: -79.8 %, 2026: -73.4 %
- **Squeeze průraz ×10**: 2023: -91.4 %, 2024: -91.7 %, 2025: -59.9 %, 2026: -86.8 %
- **BTC ×3, jen drž**: 2023: 433.4 %, 2024: 168.2 %, 2025: -9.8 %, 2026: -42.6 %

## Živý papír od 2026-11-07

| Strategie | Účet | Čistě | Obchodů | Likvidace | Otevřená pozice |
|---|---:|---:|---:|---:|---|
| Scalper 15m ×20 | 842 | -1 158 | 135 | 0 | – |
| Průraz ×25 | 1 901 | 901 | 16 | 0 | BTC short od 2026-11-19T21:00 |
| Knock-out ×50 | 578 | -1 422 | 5 | 0 | – |
| Martingale ×10 | 966 | -34 | 50 | 0 | BTC long od 2026-11-21T00:00 |
| Lovec propadů ×15 | 965 | -35 | 3 | 0 | – |
| Rotace hybnosti ×5 | 244 | -756 | 20 | 0 | – |
| Kronos ×10 | 229 | -771 | 157 | 0 | – |
| Týdenní hybnost ×3 | 1 000 | 0 | 0 | 0 | – |
| Squeeze průraz ×10 | 412 | -588 | 8 | 0 | BTC short od 2026-11-20T16:00 |
| BTC ×3, jen drž | 317 | -683 | 0 | 0 | BTC long od 2026-11-07T00:00 |

## Dispečer fází

Agent, který strategie nasazuje jen ve fázích trhu, kde dřív vydělávaly: [reports/downtown_dispatch.md](downtown_dispatch.md), výzkum v [reports/downtown_regimes.md](downtown_regimes.md).
