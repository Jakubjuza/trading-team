---
name: rychly-tym
description: Rychlý tým 6 rolí (Scout → Zprávy → Sentiment → Graf → Riziko → Rozhodnutí) s výsledkem BUY / WAIT / SKIP. Odlehčená varianta pro-analyzy nad stejnými agenty a datovým listem. Použij, když uživatel napíše „rychlý tým“, „6 botů“ nebo chce rychlé rozhodnutí místo celé desk analýzy.
argument-hint: TICKER [long|short] | prázdné = Scout vybere z watchlistu
---

# Rychlý tým (6 rolí)

Vstup: `$ARGUMENTS`

Šest rolí jde **za sebou** a každá může řetěz zastavit. Méně agentů než pro-analyza, stejná data a stejná pravidla
(poučení, veto událostí, stop za likviditou, riziko z configu). Rychlost tu znamená méně kroků, ne kratší timeframe:
setupy hledej na 1D/4H, ne na minutách.

## 0. Příprava
- Přečti `research/lessons.md` a sekce ✅/❌ v `research/knowledge.md`; relevantní body předej rolím 4–6.
- Datový list: `python3 research/factsheet.py <SYMBOL> --out research/factsheets/rychly_<COIN>_<YYYYMMDD_HHMM>.json`.
  Sekce s `error` doplní role web searchem (u každého čísla zdroj).

## 1. 🟡 Scout – co stojí za pozornost
- Ticker zadán → přeskoč, jen ověř ze `structure` a `orderflow`, že je na něm neobvyklý objem nebo pohyb.
- Ticker nezadán → agent **chart-scanner** nad `tickers` ze `scanner/config.yaml`: objem (relativní objem), pohyb (vůči ATR), momentum (trend 1D/4H). Vrať max. 3 tickery a pro každý vytvoř datový list.
- Nic neobvyklého → **SKIP** („není co obchodovat“), konec.

## 2. 🔴 Zprávy – co se právě stalo
Paralelně **news-analyst** (zprávy k minci, co je naceněno) a **events-analyst** (kalendář, Fed, regulace, geopolitika).
Každý: SKÓRE −2..+2, JISTOTA, fakta se zdrojem. VETO od events-analyst (zásadní událost v horizontu obchodu) → nejvýš **WAIT**.

## 3. 🟣 Sentiment – co lidé říkají
**sentiment-analyst**: Fear & Greed, funding, sociální sítě, stablecoiny. Odliš skutečnou poptávku od hype
(extrémní chamtivost + přeplněný funding ve směru obchodu = varování, ne potvrzení). SKÓRE a JISTOTA.

## 4. 🔵 Graf – trend, vstup, stop, cíl
**entry-exit-planner** ze sekcí `structure`, `levels`, `scenarios`: směr z 1D, vstup z 4H/1H, stop za likviditou
(ne uvnitř šumu ATR), 2 cíle před likviditou, R:R **po nákladech**. Směr nezadán → plán pro long i short, vyber lepší.
R:R po nákladech < `min_rr` z `scanner/config.yaml` → **SKIP**.

## 5. 🟢 Riziko – může obchod zmenšit nebo zamítnout
**risk-manager**: velikost podle `account_size` a `risk_pct` (nikdy víc), korelace s otevřenými pozicemi
(`research/demo_trades.jsonl`, papírové pozice skeneru), gap riziko (víkend, CME gap, události z kroku 2).
Vrátí APPROVE / REDUCE (násobek 0,5) / REJECT. REJECT → **SKIP**.

## 6. 🟠 Rozhodnutí – BUY / WAIT / SKIP
**head-trader** dostane výstupy 1–5 a poučení. Vážené skóre jen z rolí, které tu jsou:
struktura (z kroku 4) 2 · zprávy a události 1,5 · sentiment 0,5; jistota „nízká“ = poloviční váha.

| Výsledek | Podmínka | Riziko |
|---|---|---|
| **BUY** (long/short) | skóre ≥ +0,4, žádné veto, risk APPROVE/REDUCE | 1× nebo 0,5× (REDUCE, skóre < +1,0) |
| **WAIT** | skóre 0 až +0,4, nebo veto, nebo smíšené signály (víc než polovina rolí s nízkou jistotou) | 0 – jen sledovat, napiš při jaké ceně/události přehodnotit |
| **SKIP** | skóre < 0, R:R pod limitem, risk REJECT | 0 |

Downgrade o stupeň, když na obchod přímo sedí poučení z lessons.md, které mluví proti (uveď které).
Rychlý tým nemá kvant, deriváty ani debatu – při pochybnosti volí WAIT a doporučí plnou `pro-analyza`.

## 7. Záznam a odpověď
- Řádek do `research/rychly_verdicts.jsonl` (ne do verdicts.jsonl – ten patří desku a jde na Telegram):
  `{"id": "rychly:<SYMBOL>:<ISO čas>", "symbol": …, "direction": "long|short|none", "action": "BUY|WAIT|SKIP", "grade": "A|B|C|NO_TRADE", "weighted_score": …, "scores": {"struktura": …, "zprávy": …, "události": …, "sentiment": …}, "vetoes": [...], "risk": "APPROVE|REDUCE|REJECT", "risk_multiplier": 1|0.5|0, "entry": …, "stop": …, "targets": [..], "rr_net": …, "stopped_at": "<role, která řetěz zastavila, nebo null>", "lessons_used": [...], "summary": ["1. …", "2. …", "3. …", "4. …", "5. …"], "factsheet": "<cesta>", "time": "<ISO UTC>"}`
  `grade` mapuje akci na stupně desku (BUY 1× = A, BUY 0,5× = B, WAIT = C, SKIP = NO_TRADE), aby šly výsledky porovnat s pro-analyzou.
- Commitni `research/` (datový list + řádek) a pushni.
- Odpověď ve formátu z `CLAUDE.md` (5 řádků; řádek 1 = BUY/WAIT/SKIP + vážené skóre + role, která rozhodla).
  Při BUY navíc graf přes **chart-renderer** (skill chart-report).

Výsledky rychlého týmu se hodnotí stejně jako desk: až po desítkách uzavřených obchodů, po nákladech, proti buy & hold.
Česky. Fakta jen se zdrojem. Nejde o finanční poradenství.
