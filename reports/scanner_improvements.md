# Zlepšení rychlého skeneru – říjen 2026

Data: hodinové svíčky (yfinance), 2 roky (≈ 17 450 svíček na coin). Náklady 0,15 % na stranu
(poplatek 0,10 % + skluz 0,05 %, tj. ≈ 0,30 % za celý obchod). Výsledky v R **po nákladech**.
Benchmark „náhodné“ = stejné stopy (v ATR) a cíle (v R) na náhodných vstupech.
Nejde o finanční poradenství; backtest není záruka budoucích výsledků.

## 1. Výchozí stav (původní nastavení)

| | Obchody | Win % | Ø R (95% CI) | Σ R | Max. propad |
|---|---|---|---|---|---|
| BTC, ETH, SOL, XRP | 1 517 | 19,9 | −0,420 ± 0,154 | −638 | 652 R |
| 8 coinů | 2 897 | 20,2 | −0,345 ± 0,110 | −999 | 1 063 R |

Hlavní příčina: stopy 0,2–0,5 % od vstupu, zatímco náklady jsou ≈ 0,3 % ceny → jedna ztráta stojí 1,5–2,5 R.
První skutečný signál (BTC short 24. 10., stop 0,21 %) skončil na stopu za −2,44 R.

## 2. Co se změnilo (vybráno na datech BTC/ETH/SOL/XRP, prvních 70 %)

| Parametr | Dřív | Nyní | Proč |
|---|---|---|---|
| `min_stop_pct` | – | 1,5 % | stop musí být výrazně větší než náklady |
| `trend_ema` | – | 200 | long jen nad EMA 200, short jen pod |
| `breakout_volume_mult` | – | 1,5 | breakout musí mít objem ≥ 1,5× průměru |
| `skip_weekends` | ne | ano | víkendové průrazy krypta bývají falešné |
| `min_rr` | 2,0 | 1,5 | s širším stopem je R:R nižší, výsledek lepší |
| `max_open_per_direction` | – | 1 | krypto se hýbe spolu – max. 1 long a 1 short naráz |
| tickery | 4 | 8 (+ ADA, LINK, AVAX, DOGE) | víc příležitostí; pravidla ověřena i na nich |

Testováno a **zamítnuto** (na nových datech nepomohlo): 4H časový rámec, trailing stop, cíle v násobcích R, užší cíle.

## 3. Ověření

| Test | Původní Ø R | Nové Ø R | Nový max. propad |
|---|---|---|---|
| 4 coiny použité k výběru (2 roky) | −0,420 | **+0,043** | 23 R* |
| **5 coinů, které výběr neviděl** (ADA, LINK, AVAX, DOGE, BNB) | −0,361 | **+0,069** | 34 R* |
| 8 coinů, out-of-sample (posledních 30 %) | −0,660 | **+0,017 ± 0,211** | |
| 8 coinů + max. 1 otevřená pozice na směr | | **+0,080 ± 0,184** (186 obchodů/rok) | **36 R** |

\* propad po tickerech; přes všechny coiny chronologicky bez limitu pozic 96 R, s limitem 36 R.

Vstupy porážejí náhodné vstupy **u všech 8 coinů** (o +0,08 až +0,33 R) – pravidlo tedy něco zachycuje.
Čistý zisk po nákladech je ale malý a **statisticky zatím neprokázaný** (95% interval zahrnuje nulu).

### Citlivost na náklady (nové nastavení, 9 coinů)

| Náklady na stranu | Ø R |
|---|---|
| 0,00 % | +0,253 |
| 0,07 % (limitní příkazy, nízké poplatky) | +0,161 |
| **0,15 % (předpoklad)** | **+0,057** |
| 0,30 % | −0,139 |
| 0,45 % (např. Kraken taker 0,40 % + skluz) | −0,335 |

**Poplatky rozhodují víc než cokoli jiného.** Při taker poplatcích kolem 0,4 % je strategie ztrátová.

### Účet 10 000 USD, 2 roky, max. 1 otevřená pozice na směr

| Riziko na obchod | Konečný účet | Max. propad |
|---|---|---|
| 1 % | 12 706 USD | −31 % |
| 0,5 % | 11 442 USD | −17 % |
| 0,25 % | 10 737 USD | −9 % |

## 4. Doporučení

1. Dál jen **papírově**; rozhodne až několik týdnů skutečných signálů (`scanner/signals.jsonl`, uzavřené obchody v `state.json`).
2. Pro ostrý provoz burza s nízkými poplatky a **limitní příkazy** (náklady ≤ 0,07 % na stranu) – jinak výhoda zmizí.
3. Riziko na obchod spíš **0,25–0,5 %** – propad −31 % při 1 % je na tak malou výhodu moc.
4. Pondělní a čtvrteční kontrola bude dál ladit pravidla na nových datech (jen přes PR).
