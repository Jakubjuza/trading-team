---
name: skener
description: Projde watchlist, najde obchodní příležitosti podle pravidel ve watchlist.md a upozorní uživatele jen na ty, které projdou filtrem. Použij, když uživatel napíše „skener“, nebo ho spustí naplánovaná úloha.
---

# Skener příležitostí

Pravidla a tickery: `.claude/skills/skener/watchlist.md`. Log upozornění: `reports/alerts.md`.

## 1. Rychlé síto (levné)

Spusť **chart-scanner** na celý watchlist: aktuální cena (web search, se zdrojem), trend 4H/denní, nejbližší úrovně, a u každého tickeru „kandidát ano/ne + možný setup a spouštěč“. Kandidát = cena do max. vzdálenosti od spouštěče z watchlistu a setup povoleného typu.

Vyřaď kandidáty, kteří jsou v `reports/alerts.md` jako duplicita (pravidlo ve watchlistu). Nech max. N nejlepších (watchlist).

Žádný kandidát → přeskoč na krok 4 s výsledkem „bez příležitostí“.

## 2. Plná analýza kandidátů

Pro každého kandidáta postup z `CLAUDE.md` (kroky 2–9: trend/levels/volume, news/sentiment, setup-finder, entry-exit-planner, risk-manager, devils-advocate, time-machine, chart-renderer). Agentům předej pravidla z watchlistu (směr, typy setupů, účet, riziko, min. R:R, náklady).

## 3. Filtr upozornění

Upozorni jen na setup, který splní VŠE:
- devils-advocate nedal „zamítnout“, kvalita ≥ minimum z watchlistu,
- vážené R:R po nákladech ≥ minimum,
- spouštěč je do max. vzdálenosti od aktuální ceny,
- není duplicitní.

## 4. Záznam a commit

Do `reports/alerts.md` přidej řádek za každé spuštění (i prázdné):
`| datum čas (Praha) | ticker | směr | setup | spouštěč | vstup | stop | T1/T2 | R:R | upozorněno ano/ne | důvod |`

Commitni `reports/` (alerts.md, JSON, PNG pokud vznikl) a pushni do `main` (`git pull --rebase origin main` před pushem).

## 5. Upozornění

Jsou-li příležitosti: pokud je dostupný nástroj PushNotification, pošli krátkou notifikaci (ticker, směr, spouštěč, R:R). Poslední zpráva běhu = upozornění, max. 6 řádků na setup:

```
🔔 BTC LONG – retest 80k (kvalita B)
Spouštěč: 4H close > 80 000 · Vstup 80 050 · Stop 79 150 · T1 81 300 / T2 82 250
R:R 2,1 (po nákladech) · 0,09 BTC ≈ 7,3k USD, riziko 100 USD
Platí do: 26. 10. 20:00 · Hlavní riziko: FOMC 28. 10.
Graf: reports/BTC_2026-10-24.png (nebo „graf bez dat“)
Nejde o finanční poradenství.
```

Bez příležitostí: poslední zpráva je jediný řádek „Skener: bez příležitostí (BTC, ETH, SOL).“ a žádná notifikace.
