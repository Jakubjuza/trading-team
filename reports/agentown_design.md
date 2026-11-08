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
