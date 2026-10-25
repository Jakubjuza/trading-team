---
name: pro-analyza
description: Profesionální analýza obchodu desk-stylem – datový list + 8 oddělení (struktura, order flow, deriváty, makro, události a geopolitika, zprávy k minci, sentiment, kvant) + devils-advocate + head-trader verdikt A/B/C/NO_TRADE. Použij pro signály skeneru i ruční analýzu tickeru.
argument-hint: signál (id ze scanner/signals.jsonl) nebo TICKER long|short
---

# Pro analýza (desk)

Vstup: `$ARGUMENTS`

## 1. Datový list
- **Signál skeneru**: datový list je v `research/factsheets/<soubor>.json` (cesta je v signálu v poli `factsheet`). Vytvořil ho GitHub Actions s přístupem k burze, Hyperliquid a Deribit.
- **Ruční ticker**: zkus `python3 research/factsheet.py BTC/USDT --out research/factsheets/manual_<COIN>_<YYYYMMDD_HHMM>.json`. Sekce, kterým síť nedovolí data (`error`), doplní oddělení web searchem – nebo spusť GitHub workflow „Datový list“ (workflow_dispatch, vstup symbol), který list vygeneruje a commitne, a pak `git pull`.

## 2. Oddělení – paralelně, každé dostane signál + cestu k datovému listu
market-structure · orderflow-analyst · derivatives-analyst · macro-analyst · events-analyst · news-analyst · sentiment-analyst · quant-analyst

Každé vrátí SKÓRE −2..+2 pro směr obchodu, JISTOTU, FAKTA se zdroji a CO BY ZMĚNILO NÁZOR.
Světové burzy (otevírání Asie/Evropy/USA, víkend, CME gap) hodnotí macro-analyst ze sekce `sessions`; entry-exit-planner a devils-advocate je berou jako riziko časování.

## 3. Exekuce a riziko
entry-exit-planner (ověří stop/cíle vůči likviditě a nákladům) → risk-manager (velikost, korelace, gap riziko).
U signálu skeneru vstup/stop/cíle NEMĚŇ – planner jen řekne, zda jsou rozumné.

## 4. devils-advocate (pre-mortem) → head-trader
head-trader dostane vše a vrátí JSON verdikt + 5 řádků.

## 5. Záznam
- Přidej JSON verdikt jako řádek do `research/verdicts.jsonl` (jeden řádek, `signal_id` = id signálu, u ručního `manual:<ticker>:<čas>`).
- Commitni `research/` a pushni do `main` (`git pull --rebase origin main` před pushem). Workflow „Verdikty na Telegram“ pak verdikt pošle.
- Odpověď uživateli: obrázek z chart-renderer (u ruční analýzy), pak 5 řádků z verdiktu.

Měření: `python3 scanner/evaluate.py` porovnává výsledky signálů podle stupně A/B vs C/NO_TRADE – tak se ukáže, jestli desk přidává hodnotu. Nejde o finanční poradenství.
