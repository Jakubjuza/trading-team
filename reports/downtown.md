# Downtown – divoké strategie (jen papír)

Aktualizováno 2026-11-19 23:01 UTC skriptem `research/downtown.py` (pravidla stanovená předem v hlavičce).
Oddělené od desku: na skener, registr, riziko ani peníze nesahá. Každá strategie má papírový účet 1 000 USDT,
páku, reinvestici a skutečnou likvidaci; po bankrotu se vloží nových 1 000 USDT. Nejde o finanční poradenství.

## Zpětný test od 2023-01-01 (Kronos ×10 až od 1. 9. 2025)

| Strategie | Páka | Vloženo | Účet teď | Max. účet | Čistě | Max propad | Likvidace | Bankroty | Obchodů | Výher | Nejlepší měsíc | Nejhorší měsíc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Scalper 15m ×20 | 20× | 190 000 | 728 | 1 677 | -189 272 (-99.6 %) | -93.8 % | 0 | 189 | 13589 | 38.9 % | -69.0 % | -97.9 % |
| Průraz ×25 | 25× | 139 000 | 4 034 | 37 939 | -134 966 (-97.1 %) | -99.6 % | 10 | 138 | 2462 | 24.6 % | 242.1 % | -98.7 % |
| Knock-out ×50 | 50× | 227 000 | 1 088 | 71 135 | -225 912 (-99.5 %) | -99.8 % | 0 | 226 | 2009 | 22.9 % | -23.6 % | -98.1 % |
| Martingale ×10 | 10× | 1 000 | 216 | 1 013 | -784 (-78.4 %) | -80.3 % | 0 | 0 | 1735 | 46.3 % | 1.9 % | -23.8 % |
| Lovec propadů ×15 | 15× | 12 000 | 1 379 | 3 249 | -10 621 (-88.5 %) | -96.8 % | 2 | 11 | 276 | 42.4 % | 73.1 % | -83.9 % |
| Rotace hybnosti ×5 | 5× | 13 000 | 328 | 314 458 | -12 672 (-97.5 %) | -99.8 % | 1 | 12 | 2510 | 40.7 % | 3991.9 % | -99.7 % |
| Kronos ×10 | 10× | 30 000 | 838 | 1 626 | -29 162 (-97.2 %) | -93.1 % | 2 | 29 | 4273 | 43.1 % | -57.1 % | -96.1 % |
| Týdenní hybnost ×3 | 3× | 3 000 | 292 | 14 270 | -2 708 (-90.3 %) | -98.7 % | 1 | 2 | 224 | 45.5 % | 848.9 % | -94.6 % |
| Squeeze průraz ×10 | 10× | 10 000 | 406 | 13 899 | -9 594 (-95.9 %) | -99.3 % | 0 | 9 | 865 | 28.0 % | 362.2 % | -84.6 % |
| BTC ×3, jen drž | 3× | 1 000 | 8 026 | 19 821 | 7 026 (702.6 %) | -62.5 % | 0 | 0 | 0 | – | 116.3 % | -26.9 % |

Roky (čistá křivka, % za rok):

- **Scalper 15m ×20**: 2023: -97.7 %, 2024: -99.3 %, 2025: -99.4 %, 2026: -98.1 %
- **Průraz ×25**: 2023: -97.7 %, 2024: -99.8 %, 2025: -95.1 %, 2026: -83.1 %
- **Knock-out ×50**: 2023: -99.2 %, 2024: -98.6 %, 2025: -99.7 %, 2026: -96.5 %
- **Martingale ×10**: 2023: -19.8 %, 2024: -40.9 %, 2025: -21.0 %, 2026: -42.3 %
- **Lovec propadů ×15**: 2023: -80.8 %, 2024: -87.9 %, 2025: -96.3 %, 2026: -55.9 %
- **Rotace hybnosti ×5**: 2023: 2391.3 %, 2024: -89.7 %, 2025: -98.6 %, 2026: -92.1 %
- **Kronos ×10**: 2025: -97.3 %, 2026: -95.9 %
- **Týdenní hybnost ×3**: 2023: 270.2 %, 2024: -7.2 %, 2025: -79.8 %, 2026: -73.4 %
- **Squeeze průraz ×10**: 2023: -91.4 %, 2024: -91.7 %, 2025: -59.9 %, 2026: -87.6 %
- **BTC ×3, jen drž**: 2023: 433.4 %, 2024: 168.2 %, 2025: -9.8 %, 2026: -37.8 %

## Živý papír od 2026-11-07

| Strategie | Účet | Čistě | Obchodů | Likvidace | Otevřená pozice |
|---|---:|---:|---:|---:|---|
| Scalper 15m ×20 | 964 | -1 036 | 121 | 0 | ETH short od 2026-11-19T22:45 |
| Průraz ×25 | 822 | -178 | 16 | 0 | BTC short od 2026-11-19T21:00 |
| Knock-out ×50 | 578 | -1 422 | 5 | 0 | – |
| Martingale ×10 | 968 | -32 | 43 | 0 | – |
| Lovec propadů ×15 | 1 353 | 353 | 2 | 0 | – |
| Rotace hybnosti ×5 | 277 | -723 | 19 | 0 | ADA long od 2026-11-19T12:00 |
| Kronos ×10 | 218 | -782 | 144 | 0 | – |
| Týdenní hybnost ×3 | 1 000 | 0 | 0 | 0 | – |
| Squeeze průraz ×10 | 386 | -614 | 8 | 0 | – |
| BTC ×3, jen drž | 453 | -547 | 0 | 0 | BTC long od 2026-11-07T00:00 |

## Dispečer fází

Agent, který strategie nasazuje jen ve fázích trhu, kde dřív vydělávaly: [reports/downtown_dispatch.md](downtown_dispatch.md), výzkum v [reports/downtown_regimes.md](downtown_regimes.md).
