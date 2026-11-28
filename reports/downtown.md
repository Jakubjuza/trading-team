# Downtown – divoké strategie (jen papír)

Aktualizováno 2026-11-28 00:01 UTC skriptem `research/downtown.py` (pravidla stanovená předem v hlavičce).
Oddělené od desku: na skener, registr, riziko ani peníze nesahá. Každá strategie má papírový účet 1 000 USDT,
páku, reinvestici a skutečnou likvidaci; po bankrotu se vloží nových 1 000 USDT. Nejde o finanční poradenství.

## Zpětný test od 2023-01-01 (Kronos ×10 až od 1. 9. 2025)

| Strategie | Páka | Vloženo | Účet teď | Max. účet | Čistě | Max propad | Likvidace | Bankroty | Obchodů | Výher | Nejlepší měsíc | Nejhorší měsíc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Scalper 15m ×20 | 20× | 191 000 | 158 | 1 677 | -190 842 (-99.9 %) | -93.8 % | 0 | 190 | 13685 | 38.8 % | -78.2 % | -97.9 % |
| Průraz ×25 | 25× | 139 000 | 9 904 | 37 939 | -129 096 (-92.9 %) | -99.6 % | 10 | 138 | 2468 | 24.6 % | 739.8 % | -98.7 % |
| Knock-out ×50 | 50× | 227 000 | 212 | 71 135 | -226 788 (-99.9 %) | -99.8 % | 0 | 226 | 2014 | 22.9 % | -23.6 % | -98.1 % |
| Martingale ×10 | 10× | 1 000 | 215 | 1 013 | -785 (-78.5 %) | -80.3 % | 0 | 0 | 1756 | 46.2 % | 1.9 % | -23.8 % |
| Lovec propadů ×15 | 15× | 12 000 | 1 177 | 3 249 | -10 823 (-90.2 %) | -96.8 % | 2 | 11 | 278 | 42.4 % | 73.1 % | -83.9 % |
| Rotace hybnosti ×5 | 5× | 13 000 | 241 | 314 458 | -12 759 (-98.1 %) | -99.8 % | 1 | 12 | 2526 | 40.7 % | 3991.9 % | -99.7 % |
| Kronos ×10 | 10× | 30 000 | 378 | 1 626 | -29 622 (-98.7 %) | -93.1 % | 2 | 29 | 4369 | 43.2 % | -69.9 % | -96.1 % |
| Týdenní hybnost ×3 | 3× | 3 000 | 292 | 14 270 | -2 708 (-90.3 %) | -98.7 % | 1 | 2 | 224 | 45.5 % | 848.9 % | -94.6 % |
| Squeeze průraz ×10 | 10× | 10 000 | 524 | 13 899 | -9 476 (-94.8 %) | -99.3 % | 0 | 9 | 871 | 28.0 % | 362.2 % | -84.6 % |
| BTC ×3, jen drž | 3× | 1 000 | 7 576 | 19 821 | 6 576 (657.6 %) | -64.7 % | 0 | 0 | 0 | – | 116.3 % | -29.8 % |

Roky (čistá křivka, % za rok):

- **Scalper 15m ×20**: 2023: -97.7 %, 2024: -99.3 %, 2025: -99.4 %, 2026: -99.6 %
- **Průraz ×25**: 2023: -97.7 %, 2024: -99.8 %, 2025: -95.1 %, 2026: -58.4 %
- **Knock-out ×50**: 2023: -99.2 %, 2024: -98.6 %, 2025: -99.7 %, 2026: -99.3 %
- **Martingale ×10**: 2023: -19.8 %, 2024: -40.9 %, 2025: -21.0 %, 2026: -42.6 %
- **Lovec propadů ×15**: 2023: -80.8 %, 2024: -87.9 %, 2025: -96.3 %, 2026: -62.4 %
- **Rotace hybnosti ×5**: 2023: 2391.3 %, 2024: -89.7 %, 2025: -98.6 %, 2026: -94.2 %
- **Kronos ×10**: 2025: -97.3 %, 2026: -98.1 %
- **Týdenní hybnost ×3**: 2023: 270.2 %, 2024: -7.2 %, 2025: -79.8 %, 2026: -73.4 %
- **Squeeze průraz ×10**: 2023: -91.4 %, 2024: -91.7 %, 2025: -59.9 %, 2026: -84.0 %
- **BTC ×3, jen drž**: 2023: 433.4 %, 2024: 168.2 %, 2025: -9.8 %, 2026: -41.3 %

## Živý papír od 2026-11-07

| Strategie | Účet | Čistě | Obchodů | Likvidace | Otevřená pozice |
|---|---:|---:|---:|---:|---|
| Scalper 15m ×20 | 207 | -2 793 | 217 | 0 | – |
| Průraz ×25 | 2 018 | 1 018 | 22 | 0 | – |
| Knock-out ×50 | 113 | -1 887 | 10 | 0 | – |
| Martingale ×10 | 963 | -37 | 64 | 0 | BTC long od 2026-11-27T17:00 |
| Lovec propadů ×15 | 1 155 | 155 | 4 | 0 | – |
| Rotace hybnosti ×5 | 204 | -796 | 35 | 0 | LINK long od 2026-11-27T20:00 |
| Kronos ×10 | 1 083 | -917 | 240 | 0 | – |
| Týdenní hybnost ×3 | 1 000 | 0 | 0 | 0 | – |
| Squeeze průraz ×10 | 498 | -502 | 14 | 0 | – |
| BTC ×3, jen drž | 349 | -651 | 0 | 0 | BTC long od 2026-11-07T00:00 |

## Dispečer fází

Agent, který strategie nasazuje jen ve fázích trhu, kde dřív vydělávaly: [reports/downtown_dispatch.md](downtown_dispatch.md), výzkum v [reports/downtown_regimes.md](downtown_regimes.md).
