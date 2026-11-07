# Downtown – výzkum fází trhu a Dispečer (7. 11. 2026)

Zadání uživatele: najít i „brutálně“ výdělečné divoké strategie bez ohledu na pravidla desku, zjistit, ve které fázi trhu
je která strategie zisková, a vytvořit agenta, který strategie nasazuje jen v jejich fázi. Jen papír, oddělené od desku,
nejde o finanční poradenství.

Data: hodinové a 15m svíčky OKX (spot USDT) od 10/2022, stažené v GitHub Actions na výzkumné větvi
`claude/downtown-regimes` (sandbox na burzy nedosáhne). Náklady jako v Downtownu: poplatek 0,05 % a skluz 0,03 % na stranu,
funding 0,01 % za 8 h. Skript: `research/experiments/downtown_regimes.py`; produkční agent: `research/downtown_dispatch.py`.

## 1. Rešerše – nové divoké strategie (zdroje)

| Strategie (nová v testu) | Pravidla | Zdroj inspirace |
|---|---|---|
| Týdenní hybnost ×3 | long mince s nejlepším výnosem za 21 dní, přepíná denně | 3týdenní hybnost, Liu–Tsyvinski–Wu, [NBER w25882](https://www.nber.org/papers/w25882.pdf) |
| Squeeze průraz ×10 | nejužší Bollinger za 120 h, pak průraz pásma, trailing 3 ATR | volatility squeeze; „volatilní drag“ závisí na autokorelaci – [arXiv 2504.20116](https://web3.arxiv.org/pdf/2504.20116) |
| Průraz 20 dní ×5 | long na 20denním maximu, stop střed kanálu | [Quantpedia MAX(N)](https://quantpedia.com/revisiting-trend-following-and-mean-reversion-strategies-in-bitcoin/), [Concretum / Zarattini 2025](https://concretumgroup.com/catching-crypto-trends-a-tactical-approach-for-bitcoin-and-altcoins/) |
| Medvědí rotace ×5 | short nejslabší mince za 24 h, když je BTC pod EMA200 | long/short TSMOM, [arXiv 2602.11708](https://arxiv.org/html/2602.11708v1) |
| Noční BTC ×10 | ve 21:00 UTC na 10denním maximu → long do 14:00 | [Quantpedia: overnight sessions](https://quantpedia.com/how-to-profitably-trade-bitcoins-overnight-sessions/) |
| Odraz po šoku ×10 | hodinová svíčka pod −4 σ → long 12 h | přestřelení 6–24 h po šoku, [J. Economic Studies 2022](https://econpapers.repec.org/RePEc:eme:jespps:jes-09-2021-0488) |

Přepínání režimů: nejlepší doložené out-of-sample výsledky jsou na akciích ([statistical jump model, arXiv 2402.05272](https://arxiv.org/html/2402.05272v3) –
lepší Sharpe než HMM i buy & hold, ale zpoždění ~2 týdny). Pro krypto se studie s walk-forward testem meta-strategie
nenašla; rizikem je přeučení při výběru nejlepší buňky (strategie × fáze) – [PBO, Bailey a kol.](https://papers.ssrn.com/abstract=2326253).
Páka: růst klesá nad optimální pákou μ/σ² a dál vede ke krachu – [Peters & Adamou](https://arxiv.org/pdf/1101.4548).

## 2. Fáze trhu (z předchozího uzavřeného dne, bez pohledu dopředu)

trend = BTC nad / pod 200denním průměrem · pohyb = efektivita 30 dní ≥ 0,25 (trend) / pod (pila) · vola = 30denní
volatilita nad / pod mediánem roku. Podíl dní 2023–2026: býk · pila · klid 26 %, býk · pila · divoko 18 %,
medvěd · pila · divoko 12 %, medvěd · pila · klid 11 %, býk · trend · divoko 11 %, býk · trend · klid 10 %,
medvěd · trend · divoko 7 %, medvěd · trend · klid 5 %.

## 3. Hlavní zjištění

1. **Ne každá strategie má svou ziskovou fázi.** Scalper ×20, Průraz ×25, Knock-out ×50, Martingale, Lovec propadů a
   Kronos mají bez páky záporný průměr na obchod **ve všech 8 fázích** (−0,1 až −0,7 % na obchod). Prodělávají na
   nákladech: průměrný pohyb, který chytají, je menší než poplatky a skluz. Fázový filtr je nezachrání a Dispečer je
   nikdy nezapnul. Páka ztrátu jen znásobí.
2. **Hybnost je silně závislá na fázi.** Rotace hybnosti: v „býk · trend · divoko“ +0,79 % na obchod (n 249, t 2,2),
   v „býk · trend · klid“ +0,39 %, jinde záporná. Týdenní hybnost: v býčím trendu +11 až +12 % na obchod bez páky,
   v pile −0,6 až −2,7 %. Squeeze průraz: v „býk · trend · divoko“ +1,17 % (n 72), jinde kolem nuly.
3. **Filtr fází funguje i při učení jen z minulosti** (walk-forward, měsíčně, ≥ 12 obchodů, průměr > 0, t ≥ 1):

| Strategie | Páka | Slepě čistě (USDT) | Bankroty | Jen ve fázích čistě | Bankroty | Zapnuto času | Náhodné zapínání (medián) | Lepší než náhoda |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Rotace hybnosti ×5 | 5× | −10 926 | 11 | **+3 842** | 0 | 20 % | −2 128 | 98 % losů |
| Squeeze průraz ×10 | 10× | −7 845 | 7 | +127 | 0 | 9 % | −982 | 70 % |
| Týdenní hybnost ×3 | 3× | −2 708 | 2 | +182 | 0 | 6 % | −399 | 72 % |
| BTC ×3, jen drž | 3× | +3 351 | 0 | −561 | 0 | 26 % | −690 | 65 % |
| Odraz po šoku ×10 | 10× | −2 710 | 10 | −102 | 0 | 3 % | −235 | 63 % |

   Období od 1. 7. 2023 (první půlrok jen učení), účet 1 000 USDT s reinvesticí. Náhoda = stejný podíl dní zapnutý
   náhodně (60 losů). Ostatní strategie zůstaly vypnuté (0). „Jen drž“ fázový filtr zhoršil – držení BTC nejvíc vydělá
   právě ve dnech, které filtr nepozná předem.
4. **Brutální výdělek existuje, ale bez vybírání zisku se vrátí.** Rotace hybnosti jen v býčím trendu vyrostla
   z 1 000 USDT až na 117 771 (5×) nebo 205 410 USDT (3×, citlivostní varianta se 4 fázemi), a v roce 2025 většinu
   vrátila (propad −88 až −98 %). Pravidlo „při zdvojnásobení odlož 50 % zisku do trezoru“ snížilo vrchol, ale zisk
   udrželo: 5× z +3 842 na +16 711 USDT, propad z −98 % na −64 %. Nižší páka pomáhá stejně: 2–3× vychází lépe než 5×.
5. **Citlivost je velká – výsledky ber jako hypotézu.** Dispečer (jeden účet, vždy nejspolehlivější zapnutá strategie,
   trezor 50 %) vydělal ve zpětném testu **+8 280 USDT** (vloženo 2 000 kvůli jednomu bankrotu v listopadu 2025,
   hodnota 10 280, z toho trezor 9 620; roky 2023 +345 %, 2024 +134 %, 2025 −12 %, 2026 +3 %). „Jen drž ×3“ za stejné
   období +3 351. Se **stejnými pravidly a přísnějším t ≥ 2** ale skončil na **−164 USDT** – učí se tak pomalu, že
   zapne skoro jen „býk · trend · divoko“ a až pozdě. Při 14 strategiích × 8 fázích je část zapnutých buněk při t ≥ 1
   nutně náhoda. Celý zisk stojí hlavně na jedné rodině (hybnost) a na 1–2 býčích epizodách (2023 Q4 – 2024).

## 4. Závěr a co se zapojilo

- Do Downtownu přibyly **Týdenní hybnost ×3** a **Squeeze průraz ×10** (fázově závislé, slepě prodělávají).
  Průraz 20 dní, Medvědí rotace, Noční BTC a Odraz po šoku se nezařazují – v žádné fázi nenasbíraly dost obchodů
  s kladným průměrem.
- **Dispečer fází** (`research/downtown_dispatch.py`) běží jako další papírový účet Downtownu každé 4 h:
  určí fázi, měsíčně se z minulých obchodů naučí, kde která strategie vydělávala, nasadí celý účet do nejspolehlivější
  zapnuté strategie, jinak hotovost; při zdvojnásobení odloží 50 % zisku do trezoru. Pravidla s t ≥ 1 byla stanovená
  v prvním skriptu PŘED během na skutečných datech; t ≥ 2 je hlášené jako citlivostní kontrola, ne jako výběr.
  Živý papír od 8. 11. 2026. Výstup: `reports/downtown_dispatch.md` a záznam `dispecer` v `research/downtown.json`.
- Agent `.claude/agents/downtown-dispatcher.md` vysvětluje, co Dispečer dělá a proč, a hlídá, jestli živé výsledky
  odpovídají zpětnému testu. Pravidla nemění – změna jen po novém testu tímto skriptem.
- Hypotézy k dalšímu testu: vybírání zisku a nižší páka i pro ostatní účty; místo 8 pevných fází statistical jump
  model (zdroj výše); BTC dominance jako další osa (zatím jen slabý zdroj, data nejsou v sadě).

Varianty a čísla citlivosti (stejný engine, jeden účet Dispečera, trezor 50 %): 8 fází t ≥ 1 +13 437, 4 fáze t ≥ 1
+4 374, 4 fáze n ≥ 8 a t ≥ 0,5 +11 840 (1 bankrot). Výzkumné varianty měly v nabídce i 4 nezařazené strategie
(Průraz 20 dní, Medvědí rotace, Noční BTC, Odraz po šoku); produkční Dispečer vybírá jen ze strategií Downtownu,
proto se jeho výsledek (+8 280) liší.
