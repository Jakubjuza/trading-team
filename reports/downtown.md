# Downtown – divoké strategie (jen papír)

Aktualizováno 2026-11-09 06:10 UTC skriptem `research/downtown.py` (pravidla stanovená předem v hlavičce).
Oddělené od desku: na skener, registr, riziko ani peníze nesahá. Každá strategie má papírový účet 1 000 USDT,
páku, reinvestici a skutečnou likvidaci; po bankrotu se vloží nových 1 000 USDT. Nejde o finanční poradenství.

## Zpětný test od 2023-01-01 (Kronos ×10 až od 1. 9. 2025)

| Strategie | Páka | Vloženo | Účet teď | Max. účet | Čistě | Max propad | Likvidace | Bankroty | Obchodů | Výher | Nejlepší měsíc | Nejhorší měsíc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Scalper 15m ×20 | 20× | 189 000 | 636 | 1 677 | -188 364 (-99.7 %) | -93.8 % | 0 | 188 | 13482 | 38.8 % | -52.9 % | -97.9 % |
| Průraz ×25 | 25× | 139 000 | 7 609 | 37 939 | -131 391 (-94.5 %) | -99.6 % | 10 | 138 | 2448 | 24.5 % | 545.2 % | -98.7 % |
| Knock-out ×50 | 50× | 225 000 | 143 | 71 135 | -224 857 (-99.9 %) | -99.8 % | 0 | 224 | 2004 | 23.0 % | -23.6 % | -98.1 % |
| Martingale ×10 | 10× | 1 000 | 223 | 1 013 | -777 (-77.7 %) | -80.0 % | 0 | 0 | 1694 | 46.6 % | 1.9 % | -23.8 % |
| Lovec propadů ×15 | 15× | 12 000 | 1 097 | 3 249 | -10 903 (-90.9 %) | -96.8 % | 2 | 11 | 275 | 42.2 % | 73.1 % | -83.9 % |
| Rotace hybnosti ×5 | 5× | 13 000 | 974 | 314 458 | -12 026 (-92.5 %) | -99.8 % | 1 | 12 | 2497 | 40.7 % | 3991.9 % | -99.7 % |
| Kronos ×10 | 10× | 29 000 | 261 | 1 626 | -28 739 (-99.1 %) | -93.1 % | 2 | 28 | 4154 | 42.9 % | -69.9 % | -96.1 % |
| Týdenní hybnost ×3 | 3× | 3 000 | 292 | 14 270 | -2 708 (-90.3 %) | -98.7 % | 1 | 2 | 224 | 45.5 % | 848.9 % | -94.6 % |
| Squeeze průraz ×10 | 10× | 10 000 | 892 | 13 899 | -9 108 (-91.1 %) | -99.3 % | 0 | 9 | 861 | 28.1 % | 362.2 % | -84.6 % |
| BTC ×3, jen drž | 3× | 1 000 | 10 300 | 19 821 | 9 300 (930.0 %) | -62.5 % | 0 | 0 | 0 | – | 116.3 % | -26.9 % |

Roky (čistá křivka, % za rok):

- **Scalper 15m ×20**: 2023: -97.7 %, 2024: -99.3 %, 2025: -99.4 %, 2026: -98.3 %
- **Průraz ×25**: 2023: -97.7 %, 2024: -99.8 %, 2025: -95.1 %, 2026: -68.0 %
- **Knock-out ×50**: 2023: -99.2 %, 2024: -98.6 %, 2025: -99.7 %, 2026: -99.5 %
- **Martingale ×10**: 2023: -19.8 %, 2024: -40.9 %, 2025: -21.0 %, 2026: -40.3 %
- **Lovec propadů ×15**: 2023: -80.8 %, 2024: -87.9 %, 2025: -96.3 %, 2026: -64.9 %
- **Rotace hybnosti ×5**: 2023: 2391.3 %, 2024: -89.7 %, 2025: -98.6 %, 2026: -76.6 %
- **Kronos ×10**: 2025: -97.3 %, 2026: -98.6 %
- **Týdenní hybnost ×3**: 2023: 270.2 %, 2024: -7.2 %, 2025: -79.8 %, 2026: -73.4 %
- **Squeeze průraz ×10**: 2023: -91.4 %, 2024: -91.7 %, 2025: -59.9 %, 2026: -72.8 %
- **BTC ×3, jen drž**: 2023: 433.4 %, 2024: 168.2 %, 2025: -9.8 %, 2026: -20.1 %

## Živý papír od 2026-11-07

| Strategie | Účet | Čistě | Obchodů | Likvidace | Otevřená pozice |
|---|---:|---:|---:|---:|---|
| Scalper 15m ×20 | 884 | -116 | 14 | 0 | – |
| Průraz ×25 | 1 550 | 550 | 2 | 0 | – |
| Knock-out ×50 | 1 000 | 0 | 0 | 0 | – |
| Martingale ×10 | 1 001 | 1 | 2 | 0 | BTC long od 2026-11-09T04:00 |
| Lovec propadů ×15 | 1 076 | 76 | 1 | 0 | – |
| Rotace hybnosti ×5 | 823 | -177 | 6 | 0 | – |
| Kronos ×10 | 772 | -228 | 25 | 0 | – |
| Týdenní hybnost ×3 | 1 000 | 0 | 0 | 0 | – |
| Squeeze průraz ×10 | 847 | -153 | 4 | 0 | – |
| BTC ×3, jen drž | 956 | -44 | 0 | 0 | BTC long od 2026-11-07T00:00 |

## Dispečer fází

Agent, který strategie nasazuje jen ve fázích trhu, kde dřív vydělávaly: [reports/downtown_dispatch.md](downtown_dispatch.md), výzkum v [reports/downtown_regimes.md](downtown_regimes.md).
