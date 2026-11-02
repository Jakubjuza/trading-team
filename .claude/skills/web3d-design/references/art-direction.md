# Art direction pro 3D web

## Měřítko se vytváří, ne modeluje
Stejný model působí jako hračka nebo monument podle signálů okolo:
- **Velké věci** (budova, planeta, stroj): pomalý pohyb, kamera nízko a zespodu, širší objektiv (fov 50–65), objekt přesahuje záběr, mlha/prach v hloubce, drobné referenční detaily (postava, okna, světla).
- **Malé věci** (šperk, čip, produkt v dlani): rychlejší a jemné mikropohyby, delší ohnisko (fov 25–35), ostré detaily, malá hloubka ostrosti (rozmazané pozadí), kontaktní stín, čisté studiové světlo.
- **Abstraktní věci** (AI, data, nálada): částice a mřížky s jedním konkrétním vodítkem – osa, měřítko v HUD, číslo.
Vždy rozhodni, jak velký má objekt působit, a nastav podle toho kameru, rychlost a světlo.

## Světlo a materiál
- Kov a lesk potřebují environment map (RoomEnvironment nebo HDR) + jeden barevný rim light. Bez nich vypadají jako plast.
- Tři světla: key (měkké, z boku), rim (barevné, zezadu), fill (slabé). Barvy z palety.
- Tmavé pozadí: objekt odliš rim světlem a bloomem na hranách, ne zesvětlením celé scény.
- Světlé pozadí (jako „Motion instead of chrome“): sytý barevný gradient, objekt z teček nebo matný, text tmavý nebo bílý podle kontrastu.

## Typografie
- Display: charakterní (Bricolage Grotesque, Unbounded, Syne, Clash-like náhrady z Google Fonts: Familjen Grotesk, Instrument Serif pro kontrast, Big Shoulders Display pro technický styl, Silkscreen/VT323 pro pixel HUD).
- Body: klidné (IBM Plex Sans, Manrope, Work Sans).
- Mono pro HUD a popisky: IBM Plex Mono, JetBrains Mono, Space Mono.
- Nadpis velký (clamp(40px, 7vw, 96px)), lehký řez vedle tučného zvýraznění, `letter-spacing` záporný. HUD popisky malé, VELKÉ, s rozestupem.
- Vyhni se: Inter/Space Grotesk jako výchozí volbě, emoji jako ikonám, všemu na středu.

## Palety (výchozí body, uprav podle předmětu)
- **Polar chrome:** #05060a, #1b25ff, #8aa0ff, #e8ecff, akcent #ff3df2.
- **Aurora dots:** #04050d, #3ee6c6, #4d7dff, #9a6bff, text #eef1ff.
- **Industrial HUD:** #0a0a0a, #d9d9d9, #6b6b6b, akcent #ff5a1f, mřížka #1a1a1a.
- **Daylight gradient:** #2bc4ff → #0e1b4d, objekt #c9ffe9/#6f7bff, text #fff.
Neutrály lehce do odstínu akcentu, ne čistě šedé.

## Rozvržení a HUD
- Objekt mimo střed (např. 55–60 % šířky vpravo), nadpis vlevo dole, navigace nahoře tenká.
- Rohy obrazovky = informace: rohové závorky, krátké věty (ENGINEERED FOR MOTION.), rok založení, stav, souřadnice, počet částic.
- Tlačítka obdélníková s tenkým okrajem a šipkou, nebo pilulky se sklem (backdrop-filter).
- Jemná mřížka/LED textura přes pozadí sjednotí 3D a HTML.

## Pohyb
- Jeden orchestrovaný moment při načtení (intro paprsky → objekt se složí → text scramble), pak klidná smyčka.
- Všechno s dampingem (lerp 0.04–0.1), žádné lineární skoky.
- Kurzor = jemná odezva (naklonění ≤ 15°, odpuzení částic), ne divoké efekty.
- `prefers-reduced-motion`: statická poza, bez autorotace a introsekvence.

## Čemu se vyhnout (vypadá to vygenerovaně)
Fialovo-modrý gradient na bílé bez důvodu; krémová + serif + terakota; neonová zelená na černé jako jediný nápad; zaoblené karty se stínem všude; centrované všechno; lorem ipsum; „Welcome to the future“ texty; víc než jeden hlavní 3D objekt v hero.
