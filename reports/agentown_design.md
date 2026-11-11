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

## 2026-11-06 (večer) – redesign „chrome · neon · UFO“ na přání uživatele

**Zadání**: stránka působila rozházeně a některé údaje neseděly; vizuálně čistší, víc chrome, neon a UFO.

**Změněno**
- Jedna skleněná horní lišta s chromovým okrajem: logo (létající talíř) + nápis AGENTOWN chromovým písmem (Michroma), přepínač čtvrtí (Trade City · Žebříček · Downtown · Přehled), vpravo 3 živá čísla z databáze (aktivní strategie, papírové obchody z registru, Downtown živě v USDT).
- Odstraněno, co nesedělo: pás dnů 26. 10.–2. 11. (zastaralý), pevná čísla pokladny (0 obchodů / 3 pozice), záložka „DCA Town · brzy“, dlouhý návod přes scénu, „nabití (ukázka)“ v kartě budovy (u laboratorních věží místo něj skutečný papírový postup n/30). Texty jádra mají štítek „Stav k 27. 10.“, přehled města je bez starých dat.
- Karta budovy se ukáže až po klepnutí na budovu nebo na „Přehled“ (dřív zabírala třetinu obrazovky pořád).
- 3D: tmavší vesmírné nebe, chromové boky plošin s odrazy (RoomEnvironment jen pro kovové materiály), pod plošinami řada světel jako u talíře, radnice je chromový létající talíř se skleněnou kupolí, neonovým prstencem a světelným paprskem nad přistávací plošinou, nad městem krouží 3 malé talíře. Menší střešní nápisy.
- Žebříček a Downtown ve stejném stylu: chromové nadpisy, neonová linka, karty s chromovým okrajem.

**Ověření**: Playwright se skutečnou Three.js r160 (načtenou z GitHubu přes git, CDN je v sandboxu blokované) a WebGL SwiftShader, 1280 a 375 px, tmavý i světlý systémový režim (vzhled je záměrně jen tmavý), bez vodorovného posunu a bez chyb konzole. Databáze, kolekce `strategies` a `downtown`, capabilities i všechny čtvrti beze změny. Publikováno jako „Chrome · neon · UFO“.

## 2026-11-07

**Nalezené prvky**
1. Paleta příkazů (Ctrl/⌘ K): jedno místo pro hledání i akce, výsledky ve skupinách podle informační architektury a nahoře „nejlepší shoda“, ovládání jen klávesnicí – [Retool: Designing the command palette](https://retool.com/blog/designing-the-command-palette), [Superhuman: How to build a remarkable command palette](https://blog.superhuman.com/how-to-build-a-remarkable-command-palette/), [Solomon: Designing command palettes](https://solomon.io/designing-command-palettes/).
2. Porovnání položek vedle sebe: výběr 2–3 položek, zarovnané stejné údaje v řádcích, zvýraznění rozdílů a přepínač „jen rozdíly“ – [NN/g: 3 rules for better comparison tables](https://www.nngroup.com/videos/ux-rules-comparison-tables/), [Baymard: User-friendly comparison tools](https://baymard.com/blog/user-friendly-comparison-tools), [SAP Fiori: Comparison pattern](https://www.sap.com/design-system/fiori-design-web/v1-142/ui-elements/comparison-pattern/usage) (stránku se nepodařilo načíst, jen odkaz z vyhledávání).
3. Interest invokers (`interestfor`) – popovery na najetí/fokus bez JS – [MDN: Using interest invokers](https://developer.mozilla.org/en-US/docs/Web/API/Popover_API/Using_interest_invokers).

**Zapojeno**
- Paleta příkazů: tlačítko lupy v horní liště (na desktopu „Hledat Ctrl K / ⌘ K“, na mobilu jen ikona) a zkratka Ctrl/⌘ K. Nativní `<dialog>` se skupinami Čtvrti · Jádro města · Laboratoř · Downtown a „Nejlepší shoda“ nahoře; hledání bez diakritiky se zvýrazněním `<mark>` (název, typ, TF, směr, stav, štítek Downtownu), šipky + Enter, Esc zavře, prázdný stav s radou. Výběr budovy přeletí kamerou na budovu a otevře její kartu (z interiéru nejdřív vystoupí); čtvrti otevřou žebříček / Downtown / přehled. Položky se berou z aktuálních budov, takže i z živých kolekcí `strategies` a `downtown`. (Splněno odložené z 6. 11.)
- Porovnání strategií v žebříčku: u každého řádku „+ Porovnat“ (max. 3), dole přichycený pruh s výběrem, „Zrušit výběr“ a „Porovnat vedle sebe“. Dialog s tabulkou Pravidla · Backtest (vývoj, ověření + t, závěr + t, propad, obchodů/měs.) · Papírově (n, Ø R, Σ R, úspěšnost); nejlepší hodnota v řádku zlatě ★ (u propadu nejmenší), shodné řádky ztlumené, přepínač „Jen rozdíly“. Jen z polí registru (`backtest.*`, `paper.*`, `family`, `tf`, `dir`, `status`, `exit`, `filter`, `regimes`) – nic dopočítaného navíc.
- Globální Esc nezavře žebříček, když je otevřený dialog (zavře jen dialog).

**Ověření**: Playwright se skutečnou Three.js r160 (z GitHubu přes git, CDN v sandboxu blokované) a WebGL SwiftShader, 1280 a 375 px, tmavý i světlý systémový režim (vzhled záměrně jen tmavý): bez vodorovného posunu, bez chyb konzole (jen zablokované fonty); „keltner“ v paletě → 3 výsledky se zvýrazněním, Enter otevře kartu věže; porovnání 2 strategií → 6 nejlepších hodnot, „Jen rozdíly“ 8 řádků, tabulka se na 375 px vejde. Databáze, kolekce `strategies` a `downtown`, capabilities i všechny čtvrti beze změny. Publikováno jako „Design 7. 11.“.

**Odloženo**
- Interest invokers pro náhledy budov/strategií na najetí – MDN neuvádí stav podpory, na dotyku by byl jen záložní režim; zatím nepřidávat.
- Porovnání i pro Downtown (stejný vzor nad kolekcí `downtown`) – až podle ohlasu na porovnání v žebříčku.
- Světlý režim, sparkline papírové křivky a interval spolehlivosti – důvody beze změny (viz 5. 11.).

## 2026-11-07 (večer) – tři oddělené kupole a nápisy bez překryvů (na přání uživatele)

**Zadání**: Laboratoř a Downtown mají mít vlastní kupole; jedna velká kupole je překrývala a nápisy byly divně přeřezané.

**Změněno**
- Každá čtvrť má vlastní skleněnou kupoli: Trade City (r 80, uvnitř obrazovky žebříčku posunuté za okraj plošiny, r 61, výška 18–48), Laboratoř (fialová, střed z −152, r 62) a Downtown (červená, střed z 156, r 64). Kupole se nepřekrývají. Plošiny čtvrtí spojují dlouhé mosty s neonovým zábradlím, světly a branami LABORATOŘ / DOWNTOWN.
- Nápisy na střechách se kreslí navrch (budovy je neuříznou). Každý snímek se promítnou na obrazovku a ten s nižší prioritou, který by zakryl jiný nápis nebo horní lištu či kartu budovy, se schová. Pořadí: vybraná budova, jádro města, Downtown, Laboratoř (ověřené a papírové napřed), pak bližší. Schované nápisy nechytají kliknutí. Při čtení obrazovek žebříčku jsou nápisy budov skryté.
- Věže Laboratoře a Downtownu mají střešní nápisy se jménem a stavem. Malé talíře krouží uvnitř městské kupole nad obrazovkami. Výchozí kamera míří na město.
- Dispečer fází z Downtownu: fasáda „AI“ místo páky, vlastní myšlenky agenta (data přijdou z kolekce `downtown`).

**Ověření**: Playwright se skutečnou Three.js r160 a WebGL SwiftShader, 1280 a 375 px: bez chyb konzole, bez vodorovného posunu. Nápisy se nepřekrývají (kontrola promítnutím rohů nápisů), let na laboratorní věž z palety i „Ukázat ve městě“ v Downtownu míří na nové pozice. Paleta, porovnání i žebříček fungují. Databáze, kolekce `strategies` a `downtown` a capabilities beze změny. Publikováno jako „Tři kupole 7. 11.“.

## 2026-11-08

**Nalezené prvky**
1. Štítek čerstvosti dat („data z …“): čas brát z nejnovějšího záznamu v datech, ne z načtení stránky, mít pro každý přehled očekávanou frekvenci obnovy a neoznačovat jako živé, co živé není – [Basedash: Data freshness – how current your dashboard data really is](https://www.basedash.com/blog/data-freshness-how-current-your-dashboard-data-really-is), [Qualtrics: Dashboard data freshness](https://www.qualtrics.com/support/vocalize/dashboard-data-freshness/).
2. Relativní čas („před 3 hodinami“) u nedávných dat a přesné datum tam, kde na něm záleží – [Primer: RelativeTime guidelines](https://primer.style/product/components/relative-time/guidelines), [GitHub relative-time-element](https://github.com/github/relative-time-element/).
3. Plynulé otevírání oken a dialogů z „top layer“ jen v CSS (`@starting-style`, `transition-behavior: allow-discrete`, přechod `::backdrop`) s ohledem na `prefers-reduced-motion` – [Chrome for Developers: Animate to and from the top layer](https://developer.chrome.com/docs/modern-web-guidance/guides/ui-behaviors/animate-to-from-top-layer), [Frontend Masters: Animating the dialog element](https://frontendmasters.com/blog/animating-dialog/) (přesměrováno, nečteno).
4. CSS animace řízené posunem (`animation-timeline: view()`) – [codercops: View transitions & scroll animations 2026](https://blog.codercops.com/blog/css-view-transitions-scroll-animations-2026) (stav podpory v Safari/Firefoxu nebyl ověřen, článek s přehledem se nenačetl).

**Zapojeno**
- Štítek čerstvosti v hlavičce Downtownu: tečka + „data z D. M. RRRR HH:MM · před X hodinami“ (Intl.RelativeTimeFormat, česky), přesný čas a frekvence přepočtu v tooltipu, `<time datetime>`. Čas = nejnovější pole `updated` v kolekci `downtown`. Zelená pulzující tečka, když je stáří do 1,5× frekvence (6 h u 4hodinového přepočtu); jinak zlatý stav „Zpožděno“. Obnovuje se každou minutu. Stejný štítek je připravený v žebříčku (registr 1× denně, práh 36 h), ale ukáže se jen, když dokumenty v kolekci `strategies` dostanou pole `updated` – dnes ho nemají a datum poslední změny stavu v `history` není čas dat, takže se nic nepředstírá.
- Plynulé otevření palety příkazů, porovnání strategií (dialogy + ztmavení pozadí) a celostránkového žebříčku i Downtownu: krátké vyjetí a zprůhlednění přes `@starting-style`, jen při `prefers-reduced-motion: no-preference`. Zavření zůstává okamžité (spolehlivé i ve Firefoxu/Safari, kde přechod `display` při zavírání nefunguje).

**Ověření**: Playwright se skutečnou Three.js r160 (z GitHubu přes git, CDN v sandboxu blokované) a WebGL SwiftShader, 1280 a 375 px, tmavý i světlý systémový režim (vzhled záměrně jen tmavý): bez chyb konzole, bez vodorovného posunu (první verze štítku na 375 px přetékala o 137 px – opraveno zalamováním). Ze snímku z publikace štítek správně ukazuje „Zpožděno · data z 6. 11. 2026 22:55“; na živé stránce bere čas z databáze. Dialogy mají při otevření 2 běžící přechody s počáteční průhledností 0. Databáze, kolekce `strategies` a `downtown`, capabilities i všechny čtvrti beze změny. Publikováno jako „Design 8. 11.“ (verze 18).

**Odloženo**
- Animace řízené posunem (třeba odhalování karet Downtownu při posunu) – nepodařilo se ověřit podporu napříč prohlížeči; čistě dekorativní.
- Štítek čerstvosti pro žebříček – čeká na pole `updated` v kolekci `strategies` (doplnit v denní úloze, která kolekci plní; repozitář tento běh neměnil).
- Animace zavírání dialogů – vyžaduje JS záložní řešení pro Firefox/Safari; přínos malý.
- Světlý režim, sparkline papírové křivky strategií, interval spolehlivosti, porovnání pro Downtown, interest invokers – důvody beze změny (viz 5.–7. 11.).

## 2026-11-08 (večer) – statistiky jako v Downtownu pro Laboratoř a jádro (na přání uživatele)

**Zadání**: stejné statistiky jako u Downtownu u všech strategií Laboratoře i u hlavních strategií. Uživatel zvolil papírový účet 1 000 USDT s rizikem 1 % na obchod, přepínač Karty / Seznam a automatický přepočet.

**Změněno**
- Nový přepočet `research/city_accounts.py` (testy `tests/test_city_accounts.py`) a workflow „Agentown – papírové účty čtvrtí“ (`.github/workflows/city-accounts.yml`, denně 03:41 UTC po noční laboratoři) → `research/city_accounts.json`. Každá strategie: účet 1 000 USDT, riziko 1 % uzavřeného účtu na obchod, reinvestice, bez páky. Laboratoř = obchody celé historie atlasu se stejnými signály a výstupy jako papír + papír z `lab_trades.jsonl`; jádro = donchian_1d, pullback_1d (P0), pyramida (P2), ensemble (denní výnosy) + papír z `outcomes.jsonl`, `pyramid_outcomes.jsonl`, `equity_log.jsonl`. Carry, BRH a RSI(2) účet nemají (chybí zpětný test po obchodech ve stejném tvaru).
- Nová kolekce databáze `accounts` (35 dokumentů); denní úloha „Agentown – aktualizace z laboratoře“ ji teď synchronizuje spolu se `strategies`.
- Žebříček: přepínač Zobrazení Seznam / Karty (pamatuje se v prohlížeči) a v kartách přepínač Zpětný test / Papírově. Karty ve stylu Downtownu: čistě v USDT, účet, vloženo, křivka účtu, max. propad, nejdelší série ztrát (místo bankrotů a likvidací), max. účet, obchodů, výher, nejlepší/nejhorší obchod a měsíc, roky, poslední obchody, „+ Porovnat“. Řazení, filtry a hledání platí i pro karty. Jádro města má stejné karty.
- Poznámka pod kartami: zpětný test Laboratoře zahrnuje i období výběru strategie (optimistický) a složené úročení souběžných obchodů na 8 mincích dává velká čísla.

**Ověření**: pytest celé sady prošel; první běh workflow v Actions úspěšný (35 účtů). Playwright se skutečnou Three.js r160: 1280 a 375 px, tmavý i světlý režim, bez vodorovného posunu a bez chyb skriptu; hledání „keltner“ v kartách → 3 karty. Publikováno jako „Účty jako Downtown 8. 11.“ (verze 19).

## 2026-11-08 (noc) – Laboratoř jako čtvrť v horní liště (na přání uživatele)

- Nová záložka **Laboratoř** v horní liště mezi Žebříčkem a Downtownem; otevře celostránkovou čtvrť ve stylu Downtownu: štítek čerstvosti (čas přepočtu účtů), informační box, přepínač Zpětný test / Papírově, souhrn (počet účtů, v plusu, čistě dohromady, nejhlubší propad, nejvíc vydělala), karty všech strategií z registru seřazené podle čistého výsledku a pod nimi karty jádra města. „Ukázat ve městě“ přeletí kamerou na laboratorní plošinu. Laboratoř je i v paletě hledání (Ctrl K).
- Karty v Žebříčku (přepínač Seznam / Karty) zůstávají. Na mobilu je v liště 5 záložek (menší písmo, bez vodorovného posunu).
- Ověření: Playwright se skutečnou Three.js r160, 1280 a 375 px, tmavý i světlý režim, bez chyb skriptu a bez vodorovného posunu; Esc zavře čtvrť, přepnutí na Downtown ji zavře. Publikováno jako „Laboratoř v liště 8. 11.“ (verze 20).

## 2026-11-08 (noc) – 🧠 Mozek města a 4 nové kupole (na přání uživatele)

- Studie `research/experiments/brain_study.py` (pravidla stanovená předem, report `reports/brain_study.md`) prošla: vítěz „Mozek strategií“ – všechny strategie běží současně, mozek jen přesouvá váhy 1,5× / 1× / 0,5× podle fáze trhu (Sharpe testu 2,73 × 2,48 bez mozku, propad −16,5 % × −23,9 %).
- Papírový mozek `research/brain.py` (denně v workflow „Agentown – papírové účty čtvrtí“) → `research/brain.json` → kolekce `brain`, dokument `state` (synchronizuje denní úloha). Živý papír od 9. 11. 2026.
- 3D: čtyři nové kupole po stranách města s mosty – Pevnost (mint), Spořitelna (ledová), Motor (zlatá), Divočina (korálová). Věže = strategie (výška a barva podle násobku mozku, ▲ s neonovou střechou), nad kupolí nápis s podílem kapitálu a počtem ▲/▼, prstenec sílí s vahou. Paleta hledání umí přeletět ke každé kupoli.
- Horní lišta: nová záložka **Mozek** – fáze trhu (trend · pohyb · volatilita), pruh rozdělení kapitálu mezi kupole, Zpětný test od 2024 / Papírově živě, souhrn a karty účtu mozku a „všechno pořád“, kupole se čtvrtěmi (styl) a u každé strategie násobek a váha. Na mobilu se lišta se 6 záložkami posouvá do strany (stránka ne). Kamera se odsune až na 520.
- Ověření: Playwright se skutečnou Three.js r160, 1280 a 375 px, tmavý i světlý režim, bez chyb a bez vodorovného posunu stránky; přehled „Ukázat kupole“ ukáže všech 7 kupolí. Publikováno jako „Mozek a 4 kupole 8. 11.“ (verze 21).

## 2026-11-08 (noc) – 🤖 AI Lab: strategie vymyšlené AI (na přání uživatele)

- `research/ai_lab.py` (pravidla stanovená předem, report `reports/ai_lab.md`, workflow „AI Lab – strategie vymyšlené AI“ denně 04:29 UTC): čtyři vlastní nápady Clauda (Ozvěna BTC – lead-lag, Tichý průraz, Hodiny trhu, Rotace síly) a evoluce pravidel (4 340 vyzkoušených, fitness jen 2019–2023, vítěz zamčený v `research/ai_lab_genome.json`). Testem prošel jen vítěz evoluce; z 30 nejlepších pravidel evoluce prošlo ověřením 6, z 30 náhodných 0. Opravy po prvním běhu: vyřazení obchodů se stopem < 0,1 % (chyba dat) a klíč hodin u Hodin trhu.
- Agentown: záložka **AI Lab**, kupole s rotujícím „neuronovým jádrem“ za Laboratoří (most z laboratorní plošiny), věže = strategie (prošlé zeleně), nápis s počtem prošlých. Čtvrť: přepínač „Od 2024 (mimo učení)“ / „Papírově živě“, souhrn, karty účtů s pravidly a tabulkou učení / ověření / závěr, sekce Evoluce (počty, kontrola náhodou, top 10 pravidel). Kolekce `ailab`, dokument `state` (synchronizuje denní úloha).
- Ověření: Playwright se skutečnou Three.js r160, 1280 a 375 px, tmavý i světlý režim, bez chyb a bez vodorovného posunu. Publikováno jako „AI Lab 8. 11.“ (verze 22).

## 2026-11-09 – ▶ Prohlídka Agentownem (na přání uživatele)

- Tlačítko ▶ Prohlídka v horní liště (na mobilu a užším desktopu jen ikona). Kamera postupně přeletí 11 zastávek: celé město, Trade City, Laboratoř, AI Lab, Mozek, kupole Pevnost / Spořitelna / Motor / Divočina, Downtown a závěr. U každé skleněná karta v barvě čtvrti: krok x/11 s ukazatelem postupu, nadpis, popis co zóna dělá a obsahuje (počty a fáze trhu z živých dat), 2–4 body a tlačítko „Otevřít …“ pro danou čtvrť. Ovládání Zpět / Další, šipky, Esc; na mobilu spodní karta a kamera se posune, aby zóna byla nad kartou.
- Ověření: Playwright se skutečnou Three.js r160, 1280 a 375 px, tmavý i světlý režim: všech 11 kroků, bez chyb a bez vodorovného posunu; „Otevřít“ zavře prohlídku a otevře čtvrť. Publikováno jako „Prohlídka 9. 11.“ (verze 23).

## 2026-11-09 – 🤖 AI Lab jako průběžná laboratoř (na přání uživatele)

- `research/ai_lab.py --round` (workflow „AI Lab“ každou noc 02:13 UTC): jedno nové kolo evoluce se střídavým zaměřením (vše · jen short · rychlé 2–8 h · pomalé 16–32 h · jen long), přísný test (IS > 0, OOS t ≥ 2,5, HOLDOUT t ≥ 1, kolo musí porazit náhodnou kontrolu), registr max. 10 strategií z kol (`research/ai_rounds.json`), při přidání karta do Telegramu. Pravidla stanovená předem, doplněná do hlavičky skriptu.
- Kolo 1 (9. 11., „vše“): 4 204 pravidel, ověřením prošlo 22/30 (náhodných 1/30), přísným testem žádné → nic nepřidáno.
- Agentown: v AI Labu nová sekce „Průběžný výzkum · každou noc nové kolo“ (počet kol, obsazenost registru, zaměření dalšího kola, seznam kol s výsledkem); nové strategie z kol se automaticky objeví jako karty i věže v kupoli. Publikováno jako „AI Lab výzkum 9. 11.“ (verze 24).

## 2026-11-09 (denní běh designéra)

**Nalezené prvky**
1. Proud událostí (activity feed) s oddělovači dnů, slučováním souvisejících událostí („4 změny“), relativním časem s přesným časem na najetí, filtry podle aktéra a typu a navrženým prázdným stavem i koncem historie („Začátek historie“) – [SaaS UI: Activity feed & audit log UX patterns (7/2026)](https://www.saasui.design/blog/saas-activity-feed-audit-log-ux-patterns), [Stream: Activity feed design](https://getstream.io/blog/activity-feed-design/) (starší, 2017: model aktér–sloveso–objekt, agregované proudy, nulový stav).
2. Deep linking: každý stav, ke kterému se chce člověk vrátit, má mít vlastní adresu (identita v cestě, filtry v query, pozice ve fragmentu) – [Pattern Playground: Deep linking](https://pattern-playground.onrender.com/patterns/deep-linking).
3. CSS anchor positioning je od Firefoxu 147 „Baseline newly available“ (tooltipy a popovery ukotvené k prvku bez JS) – [web.dev: New to the web platform in January 2026](https://web.dev/blog/web-platform-01-2026) (tabulka verzí na stránce nesedí s textem, ověřit na MDN).

**Zapojeno – 📜 Kronika města** (nová záložka v horní liště mezi Downtownem a Přehledem, i v paletě Ctrl K)
- Celostránková čtvrť ve stylu ostatních (oranžovo-magentová linka): štítek čerstvosti (nejnovější `updated` z účtů, Downtownu, AI Labu a Mozku), informační box, souhrn 7 dní (počet papírových obchodů, čistě v USDT + výhry, poslední událost).
- Proud událostí nejnovější nahoře, oddělovače dnů (Dnes / Včera / den v týdnu, přichycené při posunu), časová osa s ikonou podle typu a barvou čtvrti. Typy: uzavřené papírové obchody (`live.last_trades` z kolekcí `accounts`, `downtown`, `ailab`, `brain`), otevřené pozice (`live.open`), změny stavu strategií (`history` v `strategies`), kola výzkumu AI (`ailab.research.rounds`) a spuštění papíru (`live.start`, jedna událost za čtvrť a den).
- Obchody jedné strategie z jednoho dne jsou sloučené („uzavřela 2 obchody · −11,64 USDT“) s rozbalovacím rozpisem. Relativní čas, přesný čas v `<time title>`. Filtrovací čipy Čtvrť × Typ s počty (prázdné kombinace vypnuté), stránkování po 14 dnech, konec „Začátek kroniky“, prázdné stavy. „Otevřít <čtvrť> →“ u každé události. Zpětné testy se nezobrazují, nic se nedopočítává navíc.
- Překreslí se při nových datech z databáze; otevření jiné čtvrti, prohlídky nebo Esc kroniku zavře.

**Ověření**: Playwright se skutečnou Three.js r160 (z GitHubu přes git, CDN v sandboxu blokované) a WebGL SwiftShader, 1280 a 375 px, tmavý i světlý systémový režim (vzhled záměrně jen tmavý): bez chyb konzole, bez vodorovného posunu; ze snímku dat 56 událostí ve 12 dnech, filtr Laboratoř → 48, „Otevřít“ otevře správnou čtvrť, Esc zavře. Opraveno při kontrole: nadpisy dnů přebíjelo pravidlo `.board h3`, tlačítka „Otevřít“ byla roztažená přes celou šířku. Databáze (stejné kolekce a čtení), capabilities i všechny čtvrti beze změny. Publikováno jako „Design 9. 11.“ (verze 25).

**Odloženo**
- Deep linking (např. `#kronika`, `#lab/<strategie>`) – stránka běží ve vloženém rámci claude.ai, adresu rámce uživatel nevidí ani nesdílí; bez ověření, že fragment projde, nemá smysl.
- Anchor positioning pro náhledy v Kronice/žebříčku – Safari podporu ověřit na MDN; zatím stačí `title`.
- Světlý režim, sparkline papírové křivky strategií, interval spolehlivosti, porovnání pro Downtown, interest invokers, animace řízené posunem – důvody beze změny (viz 5.–8. 11.).

## 2026-11-09 (večer) – 💰 $1M Future: simulace dvou let (na přání uživatele)

- Zadání: „představ si, že Agentown děláme už 2 roky a máme silné strategie – nasimuluj tu budoucnost“, kupole „$1M Future“. Výsledky se nevymýšlejí: `research/future_lab.py` (pravidla stanovená předem v hlavičce, testy `tests/test_future_lab.py`, workflow „$1M Future – simulace dvou let“, 12 paralelních úloh) spouští skutečný postup AI Labu: (A) **stroj času** – 24 měsíčních kol od 9. 11. 2024, každé vidí jen minulost, strategie obchodují až od přidání; (B) **zrychlená budoucnost** – 48 kol jen na datech do 9. 11. 2025 (t ≥ 3) a jeden závěrečný test na posledním roce. Výsledky `research/future_lab.json`, `reports/future_lab.md`, kola `research/future_rounds/`.
- Výsledek (poctivě): A – výzkum by přidal 11 strategií (t v ověření 2,69–4,74), naostro kladný průměr 7/11, průkazně jen 1; fond A (riziko 0,5 %/obchod, všechny strategie najednou) $46 z $1 000, BTC drž −2,3 %. B – 132 pravidel prošlo přísným testem, vybraných 10 mělo na závěrečném roce záporný průměr ve všech 10 případech, fond B Ø −0,08 R (t −5,5) → $12; 9/10 pravidel je „long vysoko nad EMA200“ (sázka na pokračující růst), BTC za ten rok −28,5 %.
- Agentown: záložka **$1M Future** a zlatá kupole s rotující mincí „$“ (vpravo za Laboratoří, most z laboratorní plošiny), věže = strategie obou simulací. Čtvrť: přepínač Stroj času / Zrychlená budoucnost, hlavní karta fondu s křivkou proti BTC drž (log), „Cesta k $1 000 000“ (log stupnice, přepočet tempa jen s jasným štítkem – teď „zatím ne“), box „Co simulace ukázala“ + hypotézy k testu (test v růstu i poklesu zvlášť, strop souběžného rizika fondu – nic se neměnilo), souhrn, karty strategií (účet $1 000, pravidlo, tabulka ověření × naostro / závěrečný test), časová osa 24 kol, mřížka 48 kol. Ceny v $. Paleta hledání umí otevřít $1M Future. Data jsou ve snímku stránky (simulace se nepřepočítává; kolekce `future` se čte, pokud vznikne).
- Ověření: Playwright se skutečnou Three.js r160, 1280 a 375 px, tmavý i světlý režim: bez chyb, bez vodorovného posunu; horní lišta s 9 záložkami na 1280 px bez překryvu (pod 1480 px skryté číslo Downtownu). Esc zavře, přepnutí čtvrtí funguje. Publikováno jako „$1M Future 9. 11.“ (verze 26).

## 2026-11-10 (denní běh designéra)

**Nalezené prvky**
1. Kalendářová mapa aktivity (GitHub styl: týdny × dny, 4–5 úrovní barvy, legenda „méně → více“, tooltip s počtem) – [21st.dev: React heatmap calendar components](https://21st.dev/blog/react-heatmap-calendar-components), [assistant-ui: Heat graph](https://www.assistant-ui.com/elements/heat-graph), [techinterview.org: Build a GitHub-style activity heatmap](https://www.techinterview.org/post/3233475390/build-github-style-activity-heatmap/).
2. Teplotní mapa výnosů po obdobích (řádek = strategie, sloupec = rok/měsíc, divergentní barva zisk/ztráta) z quant tearsheetů – [QuantStats (PyPI)](https://pypi.org/project/quantstats/).
3. Plynulé „dojetí“ čísla při změně hodnoty (animated number transitions) – [NumberFlow transitions (21st.dev)](https://21st.dev/@barvian/components/number-flow-transitions), [Rails Blocks: Animated number](https://railsblocks.com/docs/animated-number.md).
4. Deterministické generované avatary z názvu (gradient/hash) pro profily – [Reflex UI: gradient profile](https://www.mintlify.com/reflex-dev/reflex-ui/components/gradient-profile), [Hashvatar](https://aiuxplayground.com/playground/hashvatar-com).
5. Přehled klávesových zkratek na „?“ – [UI-Patterns: Keyboard shortcuts](https://ui-patterns.com/patterns/keyboard-shortcuts), [Salt DS: Keyboard shortcuts](https://main.saltdesignsystem.com/salt/patterns/keyboard-shortcuts).

**Zapojeno**
- Laboratoř: nová sekce „Rok po roku · výnos účtu v zpětném testu“ – tabulka účet × rok z pole `backtest.years` kolekce `accounts` (Laboratoř i jádro města), barva mint/korál podle logaritmu výnosu, čísla v % (k = tisíce), spodní řádek „v plusu X/Y“ za každý rok, šrafování = účet ještě neběžel, roky s méně než čtvrtinou účtů vynechané (s poznámkou). Prvních 12 podle čistého zisku, tlačítko „Zobrazit všech N účtů“. Na mobilu jméno nad řádkem buněk, 8 sloupců bez vodorovného posunu.
- Kronika: „Aktivita města · 8 týdnů“ – mřížka Po–Ne × týdny z událostí kroniky (respektuje filtry čtvrti a typu), 5 úrovní jantarové, dnešek s bílým rámečkem, popisek s počtem událostí a papírovým P/L dne; klepnutí skočí na den v proudu (dočte starší dny, když jsou skryté).
- Horní lišta: počty strategií, papírových obchodů a Downtown USDT při nové hodnotě z databáze plynule dojedou (700 ms, bez animace při `prefers-reduced-motion`).
- Ověření: Playwright 1280 a 375 px, tmavý i světlý režim, bez chyb skriptu a bez vodorovného posunu. Three.js z CDN v sandboxu nešla načíst (jsdelivr blokovaný), proto test se zástupným modulem – 3D scéna se tento běh neověřovala, změny se jí netýkají. Publikováno jako „Design 10. 11.“ (verze 27).

**Odloženo**
- Generované avatary strategií – hezké pro profily, ale přidaly by jen dekoraci bez dat; zvážit, až budou samostatné profily agentů.
- Přehled zkratek na „?“ – zkratek je zatím málo (Ctrl K, /, Esc), stačí patička palety příkazů.
- Mapa výnosů po měsících – v kolekci je jen `years` a řídká křivka `curve`; měsíční výnos by se musel dopočítávat z křivky.
- Světlý režim, sparkline papírové křivky strategií, interval spolehlivosti, porovnání pro Downtown, interest invokers, animace řízené posunem, deep linking – důvody beze změny (viz 5.–9. 11.).

## 2026-11-11 (denní běh designéra)

**Nalezené prvky**
1. Žebříček s trendem pořadí – u každé položky šipka ▲/▼ o kolik míst se posunula a zvýraznění nováčků – [shadcnblocks: Leaderboard with Trends](https://www.shadcnblocks.com/block/leaderboard3), [shadcn.io: Stats leaderboard with delta](https://www.shadcn.io/blocks/stats-leaderboard-with-delta), [UI-Patterns: Leaderboard](https://ui-patterns.com/patterns/leaderboard); otázka „jak se pořadí změnilo od minula“ – [PlayFab community](https://community.playfab.com/answers/24129/view.html), [CityStrides: Leaderboard rank change](https://community.citystrides.com/t/leaderboard-rank-change/29803).
2. Pilulka „nové položky“ v živém proudu: nové záznamy nepřeskočí čtenáři pod rukama, nahoře se objeví „↑ N nových“ a klepnutí vrátí nahoru – [21st.dev: New items pill](https://21st.dev/@ddoemonn/components/new-items-pill), [UX StackExchange: indikace nových položek v živém feedu](https://ux.stackexchange.com/questions/149353/approaches-to-indicate-and-handle-new-items-from-websocket-on-a-live-news-feed), [techinterview.org: Frontend real-time UX – liveness indicators](https://www.techinterview.org/post/3233475354/frontend-real-time-ux-liveness-activity-saving/).
3. Spodní navigační lišta na mobilu s položkou „Více“ v bottom sheetu – [UXPin: Mobile navigation (2026)](https://www.uxpin.com/studio/blog/mobile-navigation-examples/), [Design Studio: Mobile navigation UX (2026)](https://www.designstudiouiux.com/blog/mobile-navigation-ux/).

**Zapojeno – 👋 Od minulé návštěvy** (pamatuje si jen tento prohlížeč, `localStorage` klíč `agentown-seen-v1`; návštěva = sezení s pauzou < 1 h)
- Žebříček: pruh „Od minulé návštěvy · datum · před X“ se součty (výš / níž / nové / +N papírových obchodů / změny stavu) a čipem „Jen změněné“ (počet v čipu). U pořadí šipka ▲N / ▼N podle celkového pořadí pro zvolené řazení (tooltip „minule 4., teď 1.“), štítek „nová“, čip „+N obch.“ a „dřív <stav>“. Při první návštěvě jen vysvětlení, co se příště objeví.
- Kronika: události, které při minulé návštěvě v datech nebyly (porovnání otisků událostí, ne času – zachytí i pozdě synchronizované obchody), mají štítek NOVÉ a zvýrazněnou ikonu; čára „tady jste minule skončili“ a věta s počtem nových záznamů. Když při otevřené kronice přijdou z databáze nová data a čtenář je níž, nahoře se ukáže pilulka „↑ N nových událostí“ (klepnutím nahoru).
- Nic se nedopočítává ani nevymýšlí: porovnávají se jen data z databáze (`strategies` – pořadí, `paper.n`, `status`; kronika ze stejných kolekcí jako dosud). Kolekce, pole, zápisy i capabilities beze změny.

**Ověření**: Playwright se skutečnou Three.js r160 (z GitHubu, CDN v sandboxu blokované) a mockem databáze, 1280 a 375 px, tmavý i světlý systémový režim: bez chyb skriptu, bez vodorovného posunu; simulovaná minulá návštěva → ▲3 / ▼3 / nová / dřív ověřeno, „Jen změněné“ 4 z 25, v Kronice 4× NOVÉ + čára; nový obchod z mocku databáze při posunuté kronice → pilulka „↑ 1 nová událost“, klepnutí vrátí nahoru. Publikováno jako „Design 11. 11.“ (verze 28).

**Odloženo**
- Spodní navigace na mobilu – zásah do 3D ovládání a spodních karet (prohlídka, karta budovy), potřebuje samostatný test s živou scénou na telefonu.
- Generované avatary, přehled zkratek „?“, měsíční mapa výnosů, světlý režim, sparkline, interval spolehlivosti, porovnání pro Downtown, interest invokers, animace řízené posunem, deep linking – důvody beze změny (viz 5.–10. 11.).
