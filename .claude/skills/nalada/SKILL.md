---
name: nalada
description: Týdenní report nálady trhu – měřitelný index 1–100 (research/mood.py) doplněný o AI posouzení událostí, geopolitiky a zpráv (minulý týden, tento týden, tento měsíc). Výsledek research/mood_digest.md jde na Telegram. Spouští ho týdenní naplánovaná úloha „Nálada trhu“, jinak když uživatel napíše „nálada“ nebo chce report nálady.
---

# 🌡️ Týdenní report nálady trhu

Cíl: jedno číslo 1–100 (1 = silně medvědí, 100 = silně býčí), ze kterého je vidět, jaká nálada převládá, a krátké
zdůvodnění se zdroji. **Je to popis, ne signál** – strategie, riziko ani config se podle něj nemění
(test na historii: `reports/mood.md` – index budoucí vývoj BTC nepředpovídal).

## 1. Měřitelný index (bez AI)
- Vezmi poslední řádek `research/mood_log.jsonl` (počítá ho skener v GitHub Actions jednou denně se všemi zdroji)
  a hodnotu z doby před 7 dny. Když log chybí nebo je starší než 2 dny, spusť `python3 research/mood.py`
  (v sandboxu jsou některé zdroje blokované – chybějící složky uveď).
- Nic nepřepočítávej ručně, číslo z logu je „index“.

## 2. Události a geopolitika (AI, jen se zdroji)
Spusť paralelně agenty **events-analyst**, **news-analyst** a **macro-analyst** s datovým listem pro BTC
(`python3 research/factsheet.py BTC/USDT`; sekce `events`, `macro`, `onchain`, `options`) a s úkolem:
- co se stalo za **minulý týden** (Fed, inflace, trh práce, regulace, ETF toky, geopolitika, velké zprávy ke kryptu),
- co přijde **tento týden** a **tento měsíc** (kalendář, hlasování, expirace, termíny cel/sankcí),
- co z toho je už **naceněno** (reakce ceny, funding, implikovaný pohyb),
- skóre **−2..+2** pro „události a geopolitika“ (−2 = silně medvědí prostředí, +2 = silně býčí) a jistota.
Každé tvrzení s odkazem (URL). Co nejde ověřit, nepiš.

## 3. Výsledek
- **Index desku** = měřitelný index + 5 × AI skóre (tj. max. ±10 bodů), oříznutý na 1–100. Vždy ukaž obě čísla
  zvlášť, ať je vidět, co je měřené a co je úsudek.
- Pásma: 1–20 silně medvědí, 21–40 medvědí, 41–60 neutrální, 61–80 býčí, 81–100 silně býčí.
- Připiš řádek do `research/mood_ai.jsonl`:
  `{"date", "index", "ai_score", "ai_confidence", "desk_index", "zone"}` – po ≥ 26 týdnech mentor ověří,
  jestli AI úprava něco přidává (jinak se z reportu vypustí).

Zapiš `research/mood_digest.md` (max. ~20 řádků, česky, bez tabulek – jde na Telegram):
```
Index desku: 42/100 – medvědí (měřené 47, události −1 → −5) · před týdnem 51
Měřené složky: trend 59 · šíře 40 · volatilita 98 · makro 7 · Fear & Greed 30 · funding 45 · stablecoiny 52 · zprávy 40
Minulý týden: … (zdroj)
Tento týden: … (datum, čas Prahy, zdroj)
Tento měsíc: …
Naceněno: …
Co by náladu otočilo: býčí … / medvědí …
Popis nálady, ne signál. Nejde o finanční poradenství.
```

## 4. Odeslání
Commitni `research/mood_digest.md` a `research/mood_ai.jsonl` a pushni do main (`git pull --rebase origin main`
před pushem; při konfliktu zopakuj). Workflow „Nálada trhu na Telegram“ pošle report. Nikdy neměň
`scanner/config.yaml`, pravidla, riziko, live_trading ani tokeny.
