---
name: time-machine
description: Simuluje různé scénáře, jak se může obchod vyvinout, než do něj uživatel vloží peníze. Použij, když uživatel chce otestovat setup.
---

# Time Machine

Vstup: setup (ticker, vstup, stop-loss, cíle).

1. Historie setupu: pole `probabilities` signálu (P(zisk), P(T1), P(≥2R), Ø R strategie z historie, po nákladech) nebo sekce `history` datového listu. Když nic není, najdi minulé podobné situace a spočítej, jak dopadly (počet, win rate, průměrné R).
1b. Delší timeframe: sekce `scenarios` datového listu – rozpětí 10/50/90 % za 4, 13 a 26 týdnů (z historie při dnešní volatilitě, kalibrace v reports/scenarios.md), stav týden/měsíc a BTC cyklus. Tato rozpětí ber jako pravděpodobnosti cenových pásem; směr z nich NEodvozuj (v testu se nepotvrdil).
2. Sestav 4 scénáře: optimistický (dosáhne cílů), neutrální (boční pohyb), špatný (stop-loss), extrémní (gap přes stop). Ke každému uveď i to, kde by cena byla vůči pásmu 4 a 13 týdnů (např. „T2 leží za býčím 90% scénářem 4 týdnů → spíš výběr na T1“).
3. U každého uveď přibližnou pravděpodobnost, zisk/ztrátu v R a co by průběh signalizovalo.
4. Na konci uveď: co by musel trader udělat jinak v každém scénáři.

Důležité: jde o simulaci, ne o předpověď. Jasně označ, co vychází z historických dat a co je odhad.
