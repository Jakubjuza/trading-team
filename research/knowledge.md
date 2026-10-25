# Znalostní báze desku (mentor)

Spravuje agent **mentor** (`.claude/agents/mentor.md`), týdenní naplánovaná úloha „Mentor – znalosti a hodnocení“.
Desk ji čte před verdiktem spolu s `research/lessons.md` – hlavně sekce ✅ a ❌.

Pravidla:
- každý poznatek = **tvrzení** – zdroj (odkaz) – co z toho plyne pro náš desk – datum zápisu,
- známky: ✅ ověřeno na našich datech (odkaz na report) · 🧪 vnější důkaz, u nás neověřeno · ❌ u nás vyvráceno,
- jen ověřitelné zdroje (odborné studie, data, oficiální dokumenty); blogy a videa jen jako tip k ověření, ne jako důkaz,
- nic se nepoužije jako pravidlo skeneru, dokud to neprojde testem (předem stanovené parametry, IS/OOS, náhodné vstupy,
  náklady) – viz „Hypotézy k testu“,
- max. ~40 poznatků; slučovat podobné, nejslabší mazat.

## ✅ Ověřeno na našich datech

- **Trend na denním grafu má v kryptu výhodu i po nákladech** – donchian_1d OOS +0,18 R, pullback_1d OOS +0,15 R
  (s filtrem paniky), nad náhodnými vstupy – `reports/setup_library.md`, `reports/adaptive.md` – 25. 10. 2026.
  Shoduje se s vnějším důkazem: time-series momentum v kryptu ([Liu & Tsyvinski 2021, RFS](https://ideas.repec.org/a/oup/rfinst/v34y2021i6p2689-2727..html)),
  ve futures napříč trhy ([Moskowitz, Ooi, Pedersen 2012, JFE](https://papers.ssrn.com/abstract=2089463)).
- **Výhoda trendu od roku 2022 slábne** (Ø +0,50 → +0,15 R) – `reports/adaptive.md`; sleduje se „zdravím strategií“.
- **Nevstupovat v panice** (ATR % v horních 20 % roku) zlepšilo OOS obou denních strategií, robustní v 9 sousedních
  nastaveních – `reports/adaptive.md` – 25. 10. 2026.
- **Carry z fundingu (long spot + short perp) vydělává i v letech, kdy trend ztrácí** – +2 až +8,5 % p.a., propad do
  1,3 %, 2026 v plusu – `reports/carry.md`. Vnější důkaz: crypto carry v průměru > 10 % ročně, poháněné poptávkou po páce
  a omezeným arbitrážním kapitálem ([BIS WP 1087, Schmeling, Schrimpf, Todorov](https://www.bis.org/publications/working-paper-1087-crypto-carry)).
- **Vstup z nižších TF (1D signál → 4H/1H spouštěč) pomáhá hlavně pullbacku** (+0,104 vs. +0,015 R/signál), u Donchianu
  ne; zatím nevýznamné – papírově souběžně – `reports/mtf_entry.md`.
- **Scénáře z vol-normalizovaných výnosů jsou kalibrované** (walk-forward 2022–2026: 81–83 % v pásmu 80 %) –
  `reports/scenarios.md`.

## ❌ U nás vyvráceno (neopakovat naslepo)

- **Mean reversion RSI(2) v trendu, denní** – Ø −0,10 R, horší než náhoda – `reports/adaptive.md`.
- **Rotace dual momentum** a **držení nad SMA 200** – propady −72 až −87 %, nestabilní – `reports/adaptive.md`.
- **Filtry BTC režimu, ADX, equity křivky, walk-forward parametrů, týdenního/měsíčního trendu** – nezlepšily OOS nebo
  zhoršily 2026 – `reports/adaptive.md`.
- **Hodinový breakout-retest (brh_1h)** – OOS +0,01 R, vypnuto – `reports/setup_library.md`.
- **Sweep & reclaim na 1H jako vstup pro denní signál (H4)** – −0,03 R/signál proti dnešnímu vstupu, IS záporný –
  `reports/mtf15.md` – 25. 10. 2026.
- **Poziční styl (1W) a intradenní swing (4H)** se stejnými pravidly – OOS −0,11 až −0,29 R, korelace s denními
  strategiemi +0,24 až +0,44 – `reports/styles.md` – 25. 10. 2026.

## 🧪 Vnější důkazy (u nás neověřeno)

- **Vysoký carry (funding) předpovídá propady ceny** – [BIS WP 1087](https://www.bis.org/publications/working-paper-1087-crypto-carry).
  → hypotéza H1.
- **Proxy pozornosti investorů předpovídají výnosy kryptoměn** – [Liu & Tsyvinski 2021](https://ideas.repec.org/a/oup/rfinst/v34y2021i6p2689-2727..html).
  → hypotéza H2 (chybí nám data pozornosti).
- **Momentum bitcoinu trvá zhruba 1–8 týdnů, pak se částečně obrací** – [Hong 2017](https://www.doi.org/10.1007/s10799-016-0264-6).
  Odpovídá našemu max. držení 20 dní; delší držení by podle toho nemělo pomáhat.
- **Část výhody time-series momentum může pocházet ze škálování podle volatility** (kritika MOP 2012, shrnuto
  [Alpha Architect](https://alphaarchitect.com/cross-asset-signals-and-time-series-momentum/)). U nás už riziko na obchod
  = pevné R se stopem podle ATR – podobný efekt.

- **Spouštěč vstupu na 15M (1H potvrzení → 15M obrat)** – za 2 roky +0,28 ± 0,25 R/signál nad dnešním 1H vstupem, kladný
  v obou polovinách a na 6/8 mincích, ale OOS horší (−0,15 vs. +0,12) – `reports/mtf15.md`. Nerozhodnuto → H5.

## Metodika (proč testujeme přísně)

- **Zpětné testy se snadno přeladí**; klasický hold-out nestačí, když se zkouší hodně variant –
  [Bailey, Borwein, López de Prado, Zhu: The Probability of Backtest Overfitting](https://papers.ssrn.com/abstract=2326253).
  → u nás: varianty předem, sousední hodnoty parametrů, IS/OOS, náhodné vstupy.
- **Při mnoha testech je potřeba vyšší laťka** (t > 3 místo 2) – [Harvey, Liu, Zhu 2016, RFS](https://www.nber.org/papers/w20592).
  → u nás: změna jen při OOS zlepšení ≥ 0,05 R, ≥ 100 OOS obchodů a výhodě nad náhodou.

## Hypotézy k testu (fronta pro rutinu „Kontrola a ladění skeneru“)

| ID | Hypotéza (předem stanovená) | Zdroj | Data | Stav |
|---|---|---|---|---|
| H1 | Long signál při 7denním fundingu > 30 % p.a. dopadá hůř než ostatní longy (→ snížit stupeň / vynechat) | BIS WP 1087 | funding Hyperliquid ~1 rok – málo signálů | čeká na data |
| H2 | Prudký nárůst pozornosti (Google Trends / Wikipedie) před signálem zhoršuje výsledek longu | Liu & Tsyvinski 2021 | chybí zdroj dat | čeká na data |
| H3 | Vstupy ze sobotní/nedělní denní svíčky (UTC) dopadají hůř; varianta `skip_weekends: true` zvlášť pro pullback_1d a donchian_1d (jiné parametry se nemění) zlepší OOS Ø R o ≥ 0,05 R při ≥ 100 OOS obchodech a výhodě nad náhodou | vlastní pohled 25. 10. 2026: pullback OOS všední +0,11 vs. víkend −0,22 ± 0,25 R (n=122), Donchian +0,28 vs. +0,07 ± 0,31 (n=75); za 10 let bez rozdílu (víkend +0,44 / +0,22) – jen podezření, ne důkaz | denní data 8 mincí 2016–2026 (`scanner/evaluate.py`) | k testu v rutině „Kontrola a ladění skeneru“ |
| H4 | Sweep & reclaim na 1H (propíchnutí min/max 12 h a zavření zpět do 2 h) jako vstup pro denní signál je lepší než dnešní 1H vstup | video „timeframe ladder“ (raventraders) – jen tip | 15M OKX 11/2024–10/2026 | **neprošla** 25. 10. 2026: −0,03 ± 0,19 R/signál vs. C, IS −0,06 – `reports/mtf15.md` |
| H5 | Spouštěč na 15M (1H close vs EMA20 → 15M dotek EMA20 → 15M obratová svíčka) je lepší než dnešní 1H vstup | test 25. 10. 2026 (`reports/mtf15.md`) | nová data od 26. 10. 2026 | nerozhodnuto: celé období +0,28 R/signál, OOS −0,15 vs. +0,12 – rozhodnout na nových datech (papírově) |

## Hodnocení agentů desku

Až bude ≥ 20 uzavřených obchodů s verdiktem (`research/outcomes.jsonl` × `research/verdicts.jsonl`). Zatím 0
(kontrola 25. 10. 2026: outcomes.jsonl neexistuje, verdicts.jsonl má 1 řádek – SKIPPED).
