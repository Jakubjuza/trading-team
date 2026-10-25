# Přizpůsobení trhu a nové typy strategií (25. 10. 2026)

Otázka: dá se strategie přizpůsobit trhu tak, aby byla zisková i v nepříznivých obdobích?
Metoda: denní data 2016–2026, 8 mincí (BTC, ETH, SOL, XRP, ADA, LINK, AVAX, DOGE), náklady 0,15 % na stranu,
stejné limity jako živý skener (max. 2 otevřené pozice na strategii a směr, max. 3 nové za den). Všechny varianty
byly **stanovené předem** se standardními hodnotami; filtry vidí jen minulost. 1 R = 0,5 % účtu.
Skripty: `research/experiments/` (README tam).

## 1. Přizpůsobení stávajících strategií (Donchian + pullback, denní)

Měřeno před zapnutím filtru paniky (tehdejší config).

| Varianta | Obchodů | Ø R | Celkem R | Max. propad R | Půlroky ve ztrátě | Nejhorší půlrok R | Ø R < 2022 | Ø R ≥ 2022 | 2026 R |
|---|---|---|---|---|---|---|---|---|---|
| V0 základ | 745 | +0,283 | +210,6 | 28,2 | 20 % | −14,8 | +0,503 | +0,098 | −7,9 |
| V1 BTC režim (long jen nad EMA200 BTC) | 618 | +0,280 | +173,0 | 37,7 | 24 % | −24,8 | +0,537 | +0,055 | −10,4 |
| V2 jen trend (ADX ≥ 20) | 618 | +0,314 | +193,9 | 33,6 | 20 % | −14,9 | +0,549 | +0,104 | +0,5 |
| **V3 bez vstupu v panice** (ATR % v horních 20 % roku) | 693 | **+0,328** | **+227,4** | **25,8** | 18 % | −14,8 | +0,541 | +0,150 | −7,6 |
| V4 poloviční pozice po ztrátové sérii (20 obchodů) | 745 | +0,221 | +164,7 | 21,5 | 31 % | −10,3 | +0,456 | +0,023 | −8,6 |
| V5 pauza po ztrátové sérii (stínová equity) | 516 | +0,301 | +155,2 | 27,5 | 37 % | −15,1 | +0,539 | −0,010 | −9,9 |
| V6 rotace strategií podle výsledků | 745 | +0,250 | +185,9 | 21,1 | 27 % | −9,2 | +0,487 | +0,050 | −7,4 |
| V7 walk-forward (parametry každých 6 měsíců) | 727 | +0,283 | +205,5 | 33,7 | 18 % | −16,6 | +0,447 | +0,135 | −1,2 |
| V8 V1 + V4 | 618 | +0,234 | +144,5 | 23,6 | 31 % | −18,0 | +0,478 | +0,021 | −11,4 |

**Filtr paniky – robustnost** (okno 180/365/730 dní × vynechat horních 10/20/30 %): Ø R se zlepšil ve všech
9 nastaveních (+0,300 až +0,380 vs. +0,283), před i po 2022, na 7 z 8 mincí. Zapnut ve středovém nastavení
(365 dní, 20 %), ne v nejlepším – aby nebyl přeladěný. Oficiální vyhodnocení (`scanner/evaluate.py`):
donchian_1d OOS +0,158 → **+0,180 R**, pullback_1d OOS +0,101 → **+0,145 R**.

**Filtr podle vyššího rámce** (s filtrem paniky): jen ve směru týdne (EMA 21 týdnů) Ø +0,364 R, propad 19,5 R –
ale obchody proti týdennímu trendu nejsou výrazně horší (+0,33 vs. +0,36 R, v rámci intervalu), na 4 z 8 mincí
vychází opačně a 2026 zhoršuje ve všech délkách EMA (10–40 týdnů). **Nezapnuto** – vyšší rámec se používá pro
scénáře a riziko, ne jako filtr (viz reports/scenarios.md). Ve směru měsíce (SMA 10) horší.

## 2. Nové typy strategií

| Strategie | Výsledek | Rozhodnutí |
|---|---|---|
| Mean reversion RSI(2) v trendu, denní | −0,096 ± 0,043 R (IS −0,125, OOS −0,032, náhodné −0,013); v portfoliu propad 26 → 42 R | ❌ vypnuto (`mr_1d`) |
| Rotace dual momentum (top 3 za 28 dní, jinak hotovost) | CAGR 118 %, ale propad −87 %, nejhorší půlrok −73 %, Sharpe 1,15 vs. 1,21 u držení všech mincí; sousední nastavení ≥ 2022 od −15 % do +19 % ročně | ❌ nestabilní, propady jako držení |
| Držet minci jen nad SMA 200 dní | propad −72 % (vs. −84 % držení), CAGR 66 % (vs. 74 %), 2022 −33 % (vs. −76 %) | ❌ propady pořád obří |
| Carry z fundingu (long spot + short perp) | +2 až +8,5 % p.a. na kapitál, propad do 1,2 %, 2026 v plusu (7 z 8 mincí) | ✅ papírově |

Důležitý vedlejší výsledek: žádná „držící“ strategie se nepřiblíží řízení rizika desku – stávající strategie se
stopem a 0,5 % rizika měly největší propad ~26 R ≈ −13 % účtu, držení mincí −70 až −90 %.

## 3. Carry z fundingu

Long spot + short perpetual stejné velikosti (bez směrového rizika), inkasuje se funding. Hyperliquid, ~1 rok
historie (od 11/2024), detaily v `reports/carry.md`:

- výnos **2–8,5 % p.a.** na kapitál podle mince (BTC +5,8 %, ETH +4,8 %, LINK +8,5 %), max. propad do 1,2 %,
  nejhorší měsíc −0,35 %; **v roce 2026 v plusu u 7 z 8 mincí**, zatímco trendové strategie ztrácejí,
- pravidlo vstupu > 10 % p.a. přidalo málo proti „pořád v pozici“; vzorek je krátký,
- rizika mimo backtest: likvidace short perpu při prudkém růstu, riziko burzy, basis; vyžaduje futures účet.

Rozhodnutí: ✅ **papírově** – skener jednou denně vyhodnotí 7denní funding, oznámí 💰 vstup/výstup a sčítá výnos
(heartbeat). Na burzu se nic neposílá.

## Závěr

- Neexistuje přizpůsobení, které by udělalo každé období ziskovým; 2026 je ztrátový ve všech variantách.
- Většina „chytrých“ adaptací škodí nebo jen zmenšuje pozici (pauza po ztrátách dokonce zastaví obchodování
  těsně před zotavením).
- Zapnuto: filtr paniky (doložené malé zlepšení) a papírový carry z fundingu (jiný zdroj výnosu, který vydělával i
  v roce 2026). Scénáře na delších timeframech se používají pro rozpětí a riziko.
- Výhoda trendových strategií od 2022 slábne (Ø +0,50 → +0,15 R) – sleduje se „zdravím strategií“ v heartbeatu.

Nejde o finanční poradenství.
