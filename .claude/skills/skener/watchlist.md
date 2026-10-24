# Watchlist a pravidla skeneru

Uprav podle sebe; skener čte tento soubor při každém spuštění.

## Tickery
| Ticker | yf symbol | Poznámka |
|---|---|---|
| BTC | BTC-USD | spot, 24/7 |
| ETH | ETH-USD | spot, 24/7 |
| SOL | SOL-USD | spot, 24/7 |
| XRP | XRP-USD | spot, 24/7 |

## Pravidla
| Pole | Hodnota |
|---|---|
| Směr | long i short |
| Typy setupů | long: breakout, retest, udržení hladiny · short: breakdown, retest zespodu, odmítnutí hladiny |
| Časové rámce | 4H a denní (swing 1–5 dní) |
| Účet | 10 000 USD, hotovost (short = přes derivát/CFD, jen informativně) |
| Riziko na obchod | 1 % (100 USD) |
| Min. R:R | 2 (po skluzu 0,05 % a fee 0,1 % na stranu) |
| Max. vzdálenost spouštěče | 2 % od aktuální ceny |
| Min. kvalita | B (devils-advocate nesmí dát „zamítnout“) |
| Max. kandidátů na plnou analýzu | 2 na jedno spuštění |
| Duplicita | stejný ticker + směr + spouštěč ±0,5 % za posledních 24 h = neposílat znovu |
