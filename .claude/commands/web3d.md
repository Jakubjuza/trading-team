---
description: Postav kvalitní 3D webovou stránku (three.js) podle popisu – hero objekt, interakce, art direction, kontrola výkonu
argument-hint: <co za stránku, pro koho, jaký 3D objekt nebo nálada>
---

Použij skill **web3d-design** (složka `.claude/skills/web3d-design` nebo `~/.claude/skills/web3d-design`) a postupuj přesně podle jeho workflow (brief → art direction → výběr technik → stavba → kontrola → předání).

Zadání od uživatele:

$ARGUMENTS

Pravidla spuštění:
- **Neptej se, stav.** Zadání ber jako dostatečné. Co v něm chybí (texty, barvy, data, název, umístění), rozhodni sám podle skillu a na konci to vypiš jako „Předpoklady“.
- **Chybějící soubory nejsou důvod se zastavit.** Pokud zadání odkazuje na soubory, šablony, data nebo skripty, které neexistují, krátce je zkus najít (aktuální složka, `git ls-files`, `find` v projektu), a když nejsou, vytvoř vlastní ukázkovou verzi ve stejném formátu, jaký zadání popisuje, a pokračuj. V předání uveď, co bylo vytvořeno náhradou.
- **Kam uložit:** když zadání neříká jinak, vytvoř novou složku `web3d-<krátký-název>/` v aktuálním adresáři s `index.html` (+ případné assety). Nikdy nepřepisuj existující soubory bez výslovného pokynu – použij nový název.
- Zeptat se smíš jen tehdy, když by pokračování něco nevratně smazalo nebo přepsalo, nebo když zadání úplně chybí (prázdný příkaz) – pak jednou otázkou: „Co má stránka představovat a jaký 3D efekt chceš?“
