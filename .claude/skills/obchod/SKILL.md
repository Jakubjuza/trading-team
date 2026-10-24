---
name: obchod
description: Preset pro rychlé zadání obchodu – ticker, směr (long/short) a stop-loss. Spustí celý tým agentů s výchozím nastavením účtu a rizika. Použij, když uživatel napíše /obchod nebo zadá ticker se směrem a stopem.
argument-hint: TICKER long|short [STOP] [vstup=X] [riziko=1] [ucet=10000] [rr=2] [typy=breakout,retest,hold]
---

# Preset: obchod

Zadání od uživatele: `$ARGUMENTS`

## 1. Načti hodnoty

Pořadí: `TICKER SMĚR STOP`, pak volitelné `klíč=hodnota`. Desetinná čárka i tečka jsou OK.

| Pole | Povinné | Výchozí | Poznámka |
|---|---|---|---|
| ticker | ano | – | např. AAPL |
| směr | ano | – | `long` / `short` (také `l` / `s`) |
| stop | ne | navrhne tým | cena stop-lossu |
| vstup | ne | navrhne tým | plánovaná vstupní cena |
| riziko | ne | 1 | % účtu na obchod |
| ucet | ne | 10000 | velikost účtu v USD, hotovostní účet |
| rr | ne | 2 | minimální R:R (1:rr) |
| typy | ne | long: `breakout,retest,hold`; short: `breakdown,retest,odmitnuti` | povolené typy setupů |

Chybí ticker nebo směr → zeptej se jen na ně, nic dalšího nespouštěj.

## 2. Zkontroluj

- Long: stop musí být **pod** vstupem. Short: stop musí být **nad** vstupem. Jinak upozorni a nepokračuj.
- Před analýzou vypiš krátkou tabulku načtených hodnot (co zadal uživatel a co je výchozí).

## 3. Spusť tým

Postup podle `CLAUDE.md` (chart-scanner → trend/levels/volume → news/sentiment → setup-finder → entry-exit-planner → risk-manager → devils-advocate → time-machine). Každému agentovi předej:

- ticker, směr a povolené typy setupů (hledej jen v daném směru),
- účet, riziko v % i v USD, minimální R:R,
- stop (a vstup), pokud je zadaný: entry-exit-planner ho **ověří** vůči úrovním a volatilitě, nenahrazuje ho bez upozornění; risk-manager z něj počítá velikost pozice,
- pokyn: aktuální ceny přes web search, u každé ceny zdroj, odhady označit.

## 4. Výstup

Jeden přehled: setup, vstup/stop/cíle, R:R, velikost pozice (ks, notional, riziko v USD), rizika, scénáře z time-machine. Odpovídej česky. Nejde o finanční poradenství.
