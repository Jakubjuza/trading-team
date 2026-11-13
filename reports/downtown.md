# Downtown – divoké strategie (jen papír)

Aktualizováno 2026-11-13 19:36 UTC skriptem `research/downtown.py` (pravidla stanovená předem v hlavičce).
Oddělené od desku: na skener, registr, riziko ani peníze nesahá. Každá strategie má papírový účet 1 000 USDT,
páku, reinvestici a skutečnou likvidaci; po bankrotu se vloží nových 1 000 USDT. Nejde o finanční poradenství.

## Zpětný test od 2023-01-01 (Kronos ×10 až od 1. 9. 2025)

| Strategie | Páka | Vloženo | Účet teď | Max. účet | Čistě | Max propad | Likvidace | Bankroty | Obchodů | Výher | Nejlepší měsíc | Nejhorší měsíc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Scalper 15m ×20 | 20× | 189 000 | 301 | 1 677 | -188 699 (-99.8 %) | -93.8 % | 0 | 188 | 13522 | 38.8 % | -77.7 % | -97.9 % |
| Průraz ×25 | 25× | 139 000 | 3 451 | 37 939 | -135 549 (-97.5 %) | -99.6 % | 10 | 138 | 2457 | 24.6 % | 192.6 % | -98.7 % |
| Knock-out ×50 | 50× | 227 000 | 1 088 | 71 135 | -225 912 (-99.5 %) | -99.8 % | 0 | 226 | 2009 | 22.9 % | -23.6 % | -98.1 % |
| Martingale ×10 | 10× | 1 000 | 217 | 1 013 | -783 (-78.3 %) | -80.3 % | 0 | 0 | 1710 | 46.5 % | 1.9 % | -23.8 % |
| Lovec propadů ×15 | 15× | 12 000 | 1 379 | 3 249 | -10 621 (-88.5 %) | -96.8 % | 2 | 11 | 276 | 42.4 % | 73.1 % | -83.9 % |
| Rotace hybnosti ×5 | 5× | 13 000 | 476 | 314 458 | -12 524 (-96.3 %) | -99.8 % | 1 | 12 | 2499 | 40.7 % | 3991.9 % | -99.7 % |
| Kronos ×10 | 10× | 29 000 | 240 | 1 626 | -28 760 (-99.2 %) | -93.1 % | 2 | 28 | 4201 | 43.0 % | -69.9 % | -96.1 % |
| Týdenní hybnost ×3 | 3× | 3 000 | 292 | 14 270 | -2 708 (-90.3 %) | -98.7 % | 1 | 2 | 224 | 45.5 % | 848.9 % | -94.6 % |
| Squeeze průraz ×10 | 10× | 10 000 | 892 | 13 899 | -9 108 (-91.1 %) | -99.3 % | 0 | 9 | 861 | 28.1 % | 362.2 % | -84.6 % |
| BTC ×3, jen drž | 3× | 1 000 | 9 215 | 19 821 | 8 215 (821.5 %) | -62.5 % | 0 | 0 | 0 | – | 116.3 % | -26.9 % |

Roky (čistá křivka, % za rok):

- **Scalper 15m ×20**: 2023: -97.7 %, 2024: -99.3 %, 2025: -99.4 %, 2026: -99.2 %
- **Průraz ×25**: 2023: -97.7 %, 2024: -99.8 %, 2025: -95.1 %, 2026: -85.5 %
- **Knock-out ×50**: 2023: -99.2 %, 2024: -98.6 %, 2025: -99.7 %, 2026: -96.5 %
- **Martingale ×10**: 2023: -19.8 %, 2024: -40.9 %, 2025: -21.0 %, 2026: -41.9 %
- **Lovec propadů ×15**: 2023: -80.8 %, 2024: -87.9 %, 2025: -96.3 %, 2026: -55.9 %
- **Rotace hybnosti ×5**: 2023: 2391.3 %, 2024: -89.7 %, 2025: -98.6 %, 2026: -88.6 %
- **Kronos ×10**: 2025: -97.3 %, 2026: -98.8 %
- **Týdenní hybnost ×3**: 2023: 270.2 %, 2024: -7.2 %, 2025: -79.8 %, 2026: -73.4 %
- **Squeeze průraz ×10**: 2023: -91.4 %, 2024: -91.7 %, 2025: -59.9 %, 2026: -72.8 %
- **BTC ×3, jen drž**: 2023: 433.4 %, 2024: 168.2 %, 2025: -9.8 %, 2026: -28.5 %

## Živý papír od 2026-11-07

| Strategie | Účet | Čistě | Obchodů | Likvidace | Otevřená pozice |
|---|---:|---:|---:|---:|---|
| Scalper 15m ×20 | 419 | -581 | 54 | 0 | BTC short od 2026-11-13T17:45 |
| Průraz ×25 | 703 | -297 | 11 | 0 | – |
| Knock-out ×50 | 578 | -1 422 | 5 | 0 | – |
| Martingale ×10 | 975 | -25 | 18 | 0 | BTC long od 2026-11-13T16:00 |
| Lovec propadů ×15 | 1 353 | 353 | 2 | 0 | – |
| Rotace hybnosti ×5 | 402 | -598 | 8 | 0 | LINK long od 2026-11-13T12:00 |
| Kronos ×10 | 711 | -289 | 72 | 0 | – |
| Týdenní hybnost ×3 | 1 000 | 0 | 0 | 0 | – |
| Squeeze průraz ×10 | 847 | -153 | 4 | 0 | – |
| BTC ×3, jen drž | 717 | -283 | 0 | 0 | BTC long od 2026-11-07T00:00 |

## Dispečer fází

Agent, který strategie nasazuje jen ve fázích trhu, kde dřív vydělávaly: [reports/downtown_dispatch.md](downtown_dispatch.md), výzkum v [reports/downtown_regimes.md](downtown_regimes.md).
