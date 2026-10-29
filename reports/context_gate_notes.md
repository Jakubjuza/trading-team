# 🧠 Kontextová brána – závěry a hypotéza k ověření dopředu

Test 29. 10. 2026 (reports/context_gate.md, pravidla předem v research/experiments/context_gate.py).

## Co vyšlo
- **Brána neprošla.** Žádná ze 14 metrik kontextu (trend mince a BTC, trendovost, ADX, chop, poloha v rozpětí,
  pokračování průrazů, uklidnění, zavření svíčky, objem, přetažení, nálada) neměla v IS (2019–2023) průkazný vliv
  (|t| ≥ 2). Brána proto nic nefiltruje a skener kontext u signálů jen měří a zapisuje.
- **Překvapení proti původní hypotéze:** současné trendové strategie vydělávaly v OOS i HOLDOUTU víc, když signál
  přišel z **boční základny** (průrazy předtím nepokračovaly, slabý denní trend), než když trh už trendoval:
  HOLDOUT Ø +0,74 R vs. +0,15 R, posledních 180 dní +1,68 R vs. +0,23 R. V IS ale rozdíl nebyl (+0,49 vs. +0,46).
  Výklad: trendová strategie vydělá, když chytí ZAČÁTEK pohybu po uklidnění; když trend už běží, vstupuje pozdě.
  Protože se to ukázalo až na datech, na kterých se nic nemělo ladit, je to jen hypotéza – ne pravidlo.
- **Návrat do rozpětí v bočním trhu se nepotvrdil:** pravidlem prošla 1 kombinace z 360 (bez kontextu 2,
  v trendu 3), tj. na úrovni náhody. Kandidát (Sweep & reclaim 55 · 4H long, HOLDOUT +0,01 R) jde podle pravidel
  jen na papír a automaticky vypadne, když bude ztrátový.

## Hypotéza H1 (ověřuje se dopředu na papíře, stanoveno 29. 10. 2026)
Trendové strategie laboratoře mají vyšší Ø R u signálů s `ctx_range = true` (boční základna) než s `false`.
- Data: uzavřené obchody v research/lab_trades.jsonl + stínové v research/lab_shadow.jsonl s polem `ctx_range`.
- Vyhodnocení: až bude v každé skupině ≥ 50 uzavřených obchodů. PŘIJMOUT, když rozdíl > 0 a t ≥ 2
  (klastry po týdnech) – pak se brána přepne na „trendové strategie jen z boční základny“ (nebo vyšší váha).
  Jinak zamítnout a nic neměnit. Průběh je v pondělním souhrnu laboratoře (řádek „Brána kontextu živě“).

## Co se změnilo v papírovém obchodování hned (řízení rizika, ne strategie)
- Nejvýš 3 souběžné pozice stejného směru a 1 pozice na minci a směr (`lab.max_same_dir`), zbytek jde do stínu.
  Důvod: 28. 10. jeden pohyb BTC vybral 5 stopů naráz (identické obchody dvou strategií, 4 korelované mince).
- Výstupní cena v deníku je skutečná cena stopu/cíle, ne close svíčky.
