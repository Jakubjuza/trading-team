# Agentown – design log

Denní záznamy designéra Agentownu (https://claude.ai/artifact/HQXaGfrfq9XZhVcnFMmYi8): nalezené designové prvky, co bylo zapojeno, odloženo nebo zamítnuto. Před dalším během zkontroluj, co už tu je, a neopakuj to.

Stav stránky při založení logu (5. 11. 2026): 3D noční město (Three.js) s věžemi strategií, laboratorní čtvrť z kolekce `strategies` (db capability, zápis jen admin), kopule s 8 obrazovkami žebříčku, celostránkový žebříček (dialog) s řazením Ověření / Závěrečný test / Papírově, panel budovy (na mobilu bottom sheet), interiér věže s robotem. Záměrně jen tmavý vzhled.

## 2026-11-05

**Nalezené prvky**
1. Plynulé přeřazení řádků přes View Transitions API (same-document, bez knihovny) – [Chrome for Developers: What's new in view transitions (2025)](https://developer.chrome.com/blog/view-transitions-in-2025).
2. Filtrovací čipy s počtem položek a zaškrtnutým stavem – [Flutter/Material FilterChip](https://api.flutter.dev/flutter/material/FilterChip-class.html).
3. Žebříček, který u každé položky ukazuje velikost vzorku a nejistotu, a nováčky značí jako předběžné – [LMArena: ranking method](https://news.lmarena.ai/ranking-method), [Arena-Rank](https://news.lmarena.ai/arena-rank).
4. Živý žebříček AI obchodníků, kde rozhoduje skutečný výsledek, ne backtest – [Alpha Arena (Nof1) explained](https://www.datawallet.com/crypto/alpha-arena-nof1-ai-explained), kritika „leaderboard lied“ v [Towards AI](https://pub.towardsai.net/six-frontier-ai-models-traded-60-000-in-real-money-for-17-days-the-leaderboard-lied-to-everyone-9f73591a8d4b).

**Zapojeno (žebříček strategií)**
- Filtrovací čipy: timeframe (víc najednou), směr Vše / Long / Short, „Jen s papírovými obchody“; v čipu počet strategií, pod čipy „zobrazeno X z Y“, prázdný stav s radou zrušit filtr.
- Blok „Očekávání × papír“ u každé strategie: čekáno (ověření R/obchod) × papír Ø R × rozdíl, se středovými pruhy; ukazatel vzorku 10 dílků n/30 obchodů a štítek „malý vzorek“ pod 30. V souhrnu „papír pod očekáváním X/Y (malý vzorek)“. Jen z polí `backtest.oos_r`, `paper.n`, `paper.mean_r` – nic vymyšleného.
- Přeřazení a filtrování řádků animuje View Transitions (jen když je podpora a není `prefers-reduced-motion`), jinak se jen překreslí.
- Sloupec Papírově rozšířen (min 200 px), na mobilu vše v jednom sloupci.

**Ověření**: Playwright 1280 a 375 px, tmavý i světlý systémový režim, bez vodorovného posunu, bez chyb konzole. 3D scénu nešlo vykreslit (CDN jsdelivr je ze sandboxu blokované), proto byla Three.js nahrazena stubem; 3D kód se neměnil. Databáze, kolekce `strategies`, capabilities i všechny čtvrti beze změny.

**Odloženo**
- Světlý režim pro HUD a žebříček – stránka má záměrně jeden tmavý vzhled; kdyby se měnilo, pak celé město najednou.
- Sparkline papírové křivky u strategie – v kolekci je jen souhrn `paper`, chybí časová řada obchodů.
- Interval spolehlivosti (±) u R v ověření – v datech je jen t-statistika (`oos_t`), bez směrodatné chyby; až přibude, dát místo tečkového ukazatele.

## 2026-11-06

**Nalezené prvky**
1. Exkluzivní akordeon – nativní `<details name="…">`, kdy je otevřená vždy jen jedna sekce, bez JS knihovny – [Chrome for Developers: Exclusive accordion](https://developer.chrome.com/docs/css-ui/exclusive-accordion), [MDN Blog: Exclusive accordions using the HTML details element](https://developer.mozilla.org/en-US/blog/html-details-exclusive-accordions).
2. Živé hledání v seznamu se zvýrazněním shody a jasným prázdným stavem – [PatternFly: Search input – design guidelines](https://v5-archive.patternfly.org/components/search-input/design-guidelines), [Oracle Mobile UX: Search pattern](https://www.oracle.com/webfolder/ux/mobile/pattern/search.html).
3. Bento mřížka pro souhrnné ukazatele (dlaždice různé šířky, hlavní metrika větší) – [SaaSFrame: The bento layout trend](https://www.saasframe.io/blog/the-bento-layout-trend), [freeCodeCamp: Bento grids in web design](https://www.freecodecamp.org/news/bento-grids-in-web-design/).
4. Přehled trendů SaaS dashboardů 2026 (progresivní odkrývání detailu, klávesové zkratky v dev nástrojích) – [DEV: SaaS dashboard design trends in 2026](https://dev.to/thekitbase/saas-dashboard-design-trends-in-2026-with-examples-121m), [DEV: Five UI/UX patterns quietly defining 2026](https://dev.to/teriann_boisvert_5a7ad677/five-uiux-patterns-quietly-defining-2026-and-the-products-already-shipping-them-1mal).

**Zapojeno (žebříček strategií)**
- Profil strategie: každý řádek má rozbalovací „Profil strategie“ (exkluzivní akordeon, otevřený zůstává i po přeřazení/filtru) – pravidla (typ, parametry, výstup, filtr, režimy), tabulka testů vývoj / ověření / závěr / papír s R, t-statistikou (|t| ≥ 2 zlatě) a počtem obchodů, posledních 5 záznamů historie. Jen z polí `family`, `params`, `exit`, `filter`, `regimes`, `backtest.*_r/_t/_n`, `paper`, `history`.
- Hledání ve filtrech: bez ohledu na velikost písmen a diakritiku (název, typ, TF, směr, stav), shoda zvýrazněná `<mark>`, zkratka „/“, Esc vymaže, prázdný stav s radou; kombinuje se s čipy a počtem „zobrazeno X z Y“.
- Souhrn jako bento mřížka: 3 dlaždice počtů, „papír pod očekáváním“ zlatě a široká dlaždice „Nejlepší v ověření“ s R a t; na mobilu 2 sloupce.

**Ověření**: Playwright 1280 a 375 px, tmavý i světlý systémový režim, bez vodorovného posunu, bez chyb konzole (jen zablokované fonty v sandboxu); hledání „keltner“ → 3 z 25 se 3 zvýrazněními, akordeon drží max. 1 otevřený profil. Three.js nahrazen stubem (CDN ze sandboxu blokované), 3D kód beze změny. DB, kolekce `strategies`, capabilities a všechny čtvrti beze změny. Publikováno jako verze „Design 6. 11.“.

**Odloženo**
- Paleta příkazů (⌘K) pro skok na budovu ve 3D městě – nejde ověřit bez WebGL v sandboxu; hledání zatím jen v žebříčku.
- Profil strategie i v panelu laboratorní věže ve 3D (stejný obsah) – stejný důvod, ověřit až s funkčním vykreslením scény.
- Světlý režim, sparkline papírové křivky a interval spolehlivosti – důvody beze změny (viz 5. 11.).
