# Downtown – divoké strategie (jen papír)

Aktualizováno 2026-11-22 06:36 UTC skriptem `research/downtown.py` (pravidla stanovená předem v hlavičce).
Oddělené od desku: na skener, registr, riziko ani peníze nesahá. Každá strategie má papírový účet 1 000 USDT,
páku, reinvestici a skutečnou likvidaci; po bankrotu se vloží nových 1 000 USDT. Nejde o finanční poradenství.

## Zpětný test od 2023-01-01 (Kronos ×10 až od 1. 9. 2025)

| Strategie | Páka | Vloženo | Účet teď | Max. účet | Čistě | Max propad | Likvidace | Bankroty | Obchodů | Výher | Nejlepší měsíc | Nejhorší měsíc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Scalper 15m ×20 | 20× | 190 000 | 144 | 1 677 | -189 856 (-99.9 %) | -93.8 % | 0 | 189 | 13618 | 38.8 % | -78.2 % | -97.9 % |
| Průraz ×25 | 25× | 139 000 | 12 804 | 37 939 | -126 196 (-90.8 %) | -99.6 % | 10 | 138 | 2463 | 24.6 % | 985.7 % | -98.7 % |
| Knock-out ×50 | 50× | 227 000 | 1 088 | 71 135 | -225 912 (-99.5 %) | -99.8 % | 0 | 226 | 2009 | 22.9 % | -23.6 % | -98.1 % |
| Martingale ×10 | 10× | 1 000 | 214 | 1 013 | -786 (-78.6 %) | -80.3 % | 0 | 0 | 1747 | 46.3 % | 1.9 % | -23.8 % |
| Lovec propadů ×15 | 15× | 12 000 | 984 | 3 249 | -11 016 (-91.8 %) | -96.8 % | 2 | 11 | 277 | 42.2 % | 73.1 % | -83.9 % |
| Rotace hybnosti ×5 | 5× | 13 000 | 271 | 314 458 | -12 729 (-97.9 %) | -99.8 % | 1 | 12 | 2512 | 40.7 % | 3991.9 % | -99.7 % |
| Kronos ×10 | 10× | 30 000 | 792 | 1 626 | -29 208 (-97.4 %) | -93.1 % | 2 | 29 | 4301 | 43.1 % | -59.5 % | -96.1 % |
| Týdenní hybnost ×3 | 3× | 3 000 | 292 | 14 270 | -2 708 (-90.3 %) | -98.7 % | 1 | 2 | 224 | 45.5 % | 848.9 % | -94.6 % |
| Squeeze průraz ×10 | 10× | 10 000 | 507 | 13 899 | -9 493 (-94.9 %) | -99.3 % | 0 | 9 | 866 | 28.1 % | 362.2 % | -84.6 % |
| BTC ×3, jen drž | 3× | 1 000 | 7 479 | 19 821 | 6 479 (647.9 %) | -64.7 % | 0 | 0 | 0 | – | 116.3 % | -30.7 % |

Roky (čistá křivka, % za rok):

- **Scalper 15m ×20**: 2023: -97.7 %, 2024: -99.3 %, 2025: -99.4 %, 2026: -99.6 %
- **Průraz ×25**: 2023: -97.7 %, 2024: -99.8 %, 2025: -95.1 %, 2026: -46.2 %
- **Knock-out ×50**: 2023: -99.2 %, 2024: -98.6 %, 2025: -99.7 %, 2026: -96.5 %
- **Martingale ×10**: 2023: -19.8 %, 2024: -40.9 %, 2025: -21.0 %, 2026: -42.7 %
- **Lovec propadů ×15**: 2023: -80.8 %, 2024: -87.9 %, 2025: -96.3 %, 2026: -68.5 %
- **Rotace hybnosti ×5**: 2023: 2391.3 %, 2024: -89.7 %, 2025: -98.6 %, 2026: -93.5 %
- **Kronos ×10**: 2025: -97.3 %, 2026: -96.1 %
- **Týdenní hybnost ×3**: 2023: 270.2 %, 2024: -7.2 %, 2025: -79.8 %, 2026: -73.4 %
- **Squeeze průraz ×10**: 2023: -91.4 %, 2024: -91.7 %, 2025: -59.9 %, 2026: -84.5 %
- **BTC ×3, jen drž**: 2023: 433.4 %, 2024: 168.2 %, 2025: -9.8 %, 2026: -42.0 %

## Živý papír od 2026-11-07

| Strategie | Účet | Čistě | Obchodů | Likvidace | Otevřená pozice |
|---|---:|---:|---:|---:|---|
| Scalper 15m ×20 | 191 | -1 809 | 150 | 0 | – |
| Průraz ×25 | 2 609 | 1 609 | 17 | 0 | – |
| Knock-out ×50 | 578 | -1 422 | 5 | 0 | – |
| Martingale ×10 | 961 | -39 | 55 | 0 | – |
| Lovec propadů ×15 | 965 | -35 | 3 | 0 | – |
| Rotace hybnosti ×5 | 229 | -771 | 21 | 0 | ETH long od 2026-11-21T20:00 |
| Kronos ×10 | 206 | -794 | 172 | 0 | – |
| Týdenní hybnost ×3 | 1 000 | 0 | 0 | 0 | – |
| Squeeze průraz ×10 | 482 | -518 | 9 | 0 | – |
| BTC ×3, jen drž | 332 | -668 | 0 | 0 | BTC long od 2026-11-07T00:00 |

## Dispečer fází

Agent, který strategie nasazuje jen ve fázích trhu, kde dřív vydělávaly: [reports/downtown_dispatch.md](downtown_dispatch.md), výzkum v [reports/downtown_regimes.md](downtown_regimes.md).
