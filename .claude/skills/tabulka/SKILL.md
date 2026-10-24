---
name: tabulka
description: Pošle uživateli prázdnou tabulku se všemi hodnotami pro obchod (ticker, směr, vstup, stop, cíle, účet, riziko, pravidla…) a po jejím vyplnění vyhodnotí možnosti pozic a vstupů. Použij, když uživatel napíše „tabulka“ nebo /tabulka, nebo když pošle vyplněnou tabulku.
argument-hint: (bez argumentů) nebo vložená vyplněná tabulka
---

# Tabulka obchodu

Vstup od uživatele: `$ARGUMENTS`

## Krok 1: poslat prázdnou tabulku

Pokud uživatel jen napsal „tabulka“ (nebo argumenty jsou prázdné), pošli **přesně** obsah souboru `sablona.md` z adresáře tohoto skillu a nic dalšího nespouštěj. Na konec přidej jednu větu: „Vyplň sloupec Hodnota, prázdné pole = výchozí hodnota. Povinné jsou jen Ticker a Směr.“

## Krok 2: vyhodnotit vyplněnou tabulku

Když uživatel pošle vyplněnou tabulku (nebo řádky `pole: hodnota`):

1. **Načti hodnoty.** Prázdné pole = výchozí hodnota ze šablony. Desetinná čárka i tečka jsou OK. Chybí ticker nebo směr → zeptej se jen na ně.
2. **Zkontroluj zadání** a chyby vypiš hned nahoře:
   - long: stop < vstup < cíle; short: stop > vstup > cíle,
   - R:R každého cíle a vážené R:R podle rozdělení výstupu (poplatky a skluz započti do R),
   - velikost pozice = riziko v USD / |vstup − stop|, zaokrouhlit dolů (frakční akcie jen když je povolíš),
   - notional vs. účet a limit max. pozice; u hotovostního účtu nesmí přesáhnout účet, u marže uveď páku,
   - celkové riziko včetně otevřených pozic a jejich korelace,
   - jestli horizont držení nepřekrývá earnings nebo velká makra a jestli to sedí s pravidlem „držet přes earnings“.
3. **Zopakuj tabulku** se sloupcem „Použito“ (zadáno / výchozí / navrženo týmem).
4. **Podle pole „Rozsah analýzy“:**
   - `rychlá kontrola`: jen body 1–3 + aktuální cena přes web search (se zdrojem) a krátký verdikt,
   - `plný tým` (výchozí): postup z `CLAUDE.md` s předáním všech hodnot z tabulky. Zadané vstupy/stopy/cíle tým **ověří**, nenahrazuje je bez upozornění, a navrhne alternativy, pokud zadání nesplňuje min. R:R nebo leží ve špatném místě vůči úrovním a volatilitě.
5. **Výstup:** u plného týmu formát z `CLAUDE.md` (obrázek z chart-renderer + 5 řádků). U rychlé kontroly jen chyby zadání a 5 řádků. Česky, u každé ceny zdroj, odhady označit. Nejde o finanční poradenství.
