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

- **Přikupování do vydělávající pozice (pyramiding, P2)** – start 0,5 R, +1 kus za každý +1 ATR (max. 4), stop po přidání
  − 2 ATR, trailing 3 ATR, max. 20 dní: Ø +0,70 vs. +0,33 R, MAR 2,04 vs. 0,89, odložený rok +28,7 vs. +2,4 R, robustní
  v sousedních nastaveních – `reports/pyramid.md` – 25. 10. 2026. Od 25. 10. 2026 běží jako samostatná papírová část 🔺 Pyramida (scanner/pyramid.py) – ověření naživo.

- **Donchian ensemble s cílovou volatilitou** (5 kanálů 10–160 dní, jen long, 40 % vol na minci) – +19 %/rok, Sharpe 1,24,
  IS/OOS 1,42/1,47; s jádrem korelace −0,03, kombinace Sharpe 1,86 – `reports/portfolio_review.md` – 26. 10. 2026.
  Shoda se studií Zarattini a kol. Od 26. 10. 2026 běží jako 🧭 Ensemble (papír + spotové demo).

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

- **15M vstup do začínajícího uptrendu po krachu a panice (vyšší maxima/minima, malé svíčky)** – 60 vstupů, trailing
  Ø −0,04 ± 0,42 R ≈ náhoda; nízký objem −0,36 R, cíle 10–20R se netrefí – `reports/recovery.md` – 25. 10. 2026.
- **Obrat po prudkém pohybu (≥ 4 ATR za 4 h) s těsným stopem na 15M, cíle 10–50R** – 1 177 pokusů, Ø −0,22 až −0,42 R,
  horší než náhoda; výzva 100 USD → ztráta účtu ve 100 % simulací – `reports/reversal.md` – 25. 10. 2026.
- **Průraz ve směru pohybu na 15M s těsným stopem (0,3–1,5 %) a posouváním stopu (BE + trailing, schody, chandelier)** –
  10 280 spouštěčů, Ø −0,07 až −0,12 R po nákladech 0,07 %, o 0,02–0,05 R lepší než náhoda, ale záporné; účet 1 000 USD
  při riziku 1 % → 103–421 USD, při **5–10 % → 0–2 USD** – `reports/scalp15.md` – 26. 10. 2026.
- **Dokupování při poklesu ≥ 20 % (kus 0,25 účtu, max. 1,5×), řez poloviny při −15 % a znovuotevření níž / na místě** –
  Ø +10 % na kampaň vs. jeden nákup +18,7 % a náhodné starty +10,3 %; OOS ≈ 0; portfolio 45–87 tis. vs. buy & hold
  345 tis. USD – `reports/scale_in.md` – 26. 10. 2026. Dokupovat do zisku (pyramid) ano, do ztráty ne.
  Zrcadlový short (dokupování shortu při růstu) Ø −4 až −12 % na kampaň, likvidace; long nad / short pod SMA200
  horší než jeden vstup, OOS záporné; short pod SMA200 Ø −3 %. 15M průraz: long i short zvlášť −0,07 až −0,13 R.
- **1H vstupy oběma směry bez denního směru** a **pevné cíle 2R/4R s držením 5 dní** – Ø −0,05 / −0,04 R –
  `reports/bias_entry.md` – 26. 10. 2026. Denní směr a nechat obchod běžet jsou podstatné.
- **Long BTC 21:00–23:00 UTC** – před náklady +0,04 %/den, po nákladech −0,10 až −0,26 % – `reports/portfolio_review.md`.
- **Chycení kapitulace (long po panice: −30 % od maxima, top 10 % volatility, Fear & Greed < 20, sweep & reclaim)** –
  30 obchodů, Ø +0,30 ± 0,83 R vs. náhoda +0,34; zisk ze 2 obchodů, stop medián 11 % – `reports/capitulation.md` – 25. 10. 2026.
- **Stejné denní strategie na hlavních měnových párech** – OOS −0,24 R, pod náhodou – `reports/markets.md` – 25. 10. 2026.
  Na 8 tech akciích +0,27 R, ale náhodné vstupy +0,22 R (výběr vítězů) – výhoda strategie malá.
- **Optimalizace výstupů a filtrů denních strategií (72 nastavení × 5 vah)** – walk-forward MAR 0,77 vs. dnešní 0,83,
  odložený rok bez rozdílu – `reports/optimize.md` – 25. 10. 2026. Výběr „nejlepšího“ z historie je přeladěný.
- **Spouštěč vstupu na 15M (1H potvrzení → 15M obrat)** – za 2 roky +0,28 ± 0,25 R/signál nad dnešním 1H vstupem, kladný
  v obou polovinách a na 6/8 mincích, ale OOS horší (−0,15 vs. +0,12) – `reports/mtf15.md`. Nerozhodnuto → H5.

## Metodika (proč testujeme přísně)

- **Zpětné testy se snadno přeladí**; klasický hold-out nestačí, když se zkouší hodně variant –
  [Bailey, Borwein, López de Prado, Zhu: The Probability of Backtest Overfitting](https://papers.ssrn.com/abstract=2326253).
  → u nás: varianty předem, sousední hodnoty parametrů, IS/OOS, náhodné vstupy.
- **Při mnoha testech je potřeba vyšší laťka** (t > 3 místo 2) – [Harvey, Liu, Zhu 2016, RFS](https://www.nber.org/papers/w20592).
  → u nás: změna jen při OOS zlepšení ≥ 0,05 R, ≥ 100 OOS obchodů a výhodě nad náhodou.

- **Index nálady (trend, šíře trhu, volatilita, makro) jako předpověď směru BTC** – od 2022 korelace s výnosem
  7/30/90 dní +0,03 až +0,09, pásma neseřazená; slouží jen jako popis nálady – `reports/mood.md` – 26. 10. 2026.
- **Smart DCA (pool na propady) a lotový DCA bot (TP/SL na každý nákup)** – horší než obyčejné DCA na BTC/ETH/SOL ve
  všech variantách (rolling 3 roky: smart DCA vyhrál v 0–20 % období) – test v chatu 26. 10. 2026.

## Hypotézy k testu (fronta pro rutinu „Kontrola a ladění skeneru“)

| ID | Hypotéza (předem stanovená) | Zdroj | Data | Stav |
|---|---|---|---|---|
| H1 | Long signál při 7denním fundingu > 30 % p.a. dopadá hůř než ostatní longy (→ snížit stupeň / vynechat) | BIS WP 1087 | funding Hyperliquid ~1 rok – málo signálů | čeká na data |
| H2 | Prudký nárůst pozornosti (Google Trends / Wikipedie) před signálem zhoršuje výsledek longu | Liu & Tsyvinski 2021 | chybí zdroj dat | čeká na data |
| H3 | Vstupy ze sobotní/nedělní denní svíčky (UTC) dopadají hůř; varianta `skip_weekends: true` zvlášť pro pullback_1d a donchian_1d (jiné parametry se nemění) zlepší OOS Ø R o ≥ 0,05 R při ≥ 100 OOS obchodech a výhodě nad náhodou | vlastní pohled 25. 10. 2026: pullback OOS všední +0,11 vs. víkend −0,22 ± 0,25 R (n=122), Donchian +0,28 vs. +0,07 ± 0,31 (n=75); za 10 let bez rozdílu (víkend +0,44 / +0,22) – jen podezření, ne důkaz | denní data 8 mincí 2016–2026 (`scanner/evaluate.py`) | k testu v rutině „Kontrola a ladění skeneru“ |
| H4 | Sweep & reclaim na 1H (propíchnutí min/max 12 h a zavření zpět do 2 h) jako vstup pro denní signál je lepší než dnešní 1H vstup | video „timeframe ladder“ (raventraders) – jen tip | 15M OKX 11/2024–10/2026 | **neprošla** 25. 10. 2026: −0,03 ± 0,19 R/signál vs. C, IS −0,06 – `reports/mtf15.md` |
| H5 | Spouštěč na 15M (1H close vs EMA20 → 15M dotek EMA20 → 15M obratová svíčka) je lepší než dnešní 1H vstup | test 25. 10. 2026 (`reports/mtf15.md`) | nová data od 26. 10. 2026 | nerozhodnuto: celé období +0,28 R/signál, OOS −0,15 vs. +0,12 – rozhodnout na nových datech (papírově) |
| H6 | Donchian: celá pozice bez výběru na T1, držení až 60 dní, trailing 4 ATR, bez víkendových vstupů (pullback beze změny) má lepší poměr zisku k propadu než dnešní výstup | optimalizace 25. 10. 2026 (`reports/optimize.md`) – vzorec vybraný ve všech 5 krocích walk-forwardu, ale celý postup výběru dnešek neporazil | nová data od 26. 10. 2026 | nerozhodnuto – rozhodnout na nových datech (papírově) |
| H7 | Směr z denního grafu (Close vs. EMA200 + sklon EMA50) a průběžné vstupy na 1H (návrat k EMA20 + obratová svíčka), trailing 3 denní ATR, max. 20 dní – vydělá víc R za rok než čekání na denní signál | test 26. 10. 2026 (`reports/bias_entry.md`): +0,10 ± 0,16 R, +45 vs. +30 R/rok, neprůkazné | nová data od 26. 10. 2026 | nerozhodnuto – kandidát na papírové ověření |
| H8 | AI úprava týdenního indexu nálady (události a geopolitika, ±10 bodů) zlepší vztah indexu k výnosu BTC za další 4 týdny (korelace AI skóre s výnosem > 0,2 a vyšší než u měřeného indexu) | vlastní, 26. 10. 2026 | `research/mood_ai.jsonl` – týdenně | čeká na data (≥ 26 týdnů) |

## Hodnocení agentů desku

Až bude ≥ 20 uzavřených obchodů s verdiktem (`research/outcomes.jsonl` × `research/verdicts.jsonl`). Zatím 0
(kontrola 25. 10. 2026: outcomes.jsonl neexistuje, verdicts.jsonl má 1 řádek – SKIPPED).
