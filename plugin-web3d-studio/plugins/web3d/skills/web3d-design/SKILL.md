---
name: web3d-design
description: Navrhne a postaví kvalitní 3D webovou stránku nebo hero sekci v three.js/WebGL – roje částic a přelévání tvarů, chromové a perleťové objekty, rozložené vrstvy produktu, světelné paprsky, glitch typografie, HUD/LED rozhraní, scroll a kurzorová interakce. Použij, když uživatel napíše /web3d, chce "3D web", "3D landing page", "three.js stránku", "web jako z Awwwards", nebo má postavit produktovou či značkovou stránku s 3D efektem.
---

# Web3D design

Cíl: stránka, která vypadá jako práce dobrého motion/3D studia, ne jako šablona. 3D tu není dekorace – je to hlavní sdělení stránky. Každá stránka má **jeden hlavní moment** (hero objekt + jedna interakce) a všechno ostatní ho podporuje.

Před stavbou si přečti podle potřeby:
- `references/techniques.md` – katalog technik s funkčním kódem (vyber 1–3, ne všechny).
- `references/art-direction.md` – měřítko, světlo, typografie, palety, HUD detaily, čemu se vyhnout.
- `references/performance.md` – rozpočty, mobil, přístupnost, fallbacky.
- `templates/starter.html` – kostra stránky (renderer, post-processing, scroll, kurzor, HUD, fallback). Začínej z ní.
- `templates/particle-morph.html` – hotová ukázka roje částic přelévajícího se mezi tvary.

## Režim: stav, neptej se
- Uživatel chce hotovou stránku, ne dotazník. Nezastavuj se kvůli chybějícím detailům ani souborům.
- Odkazuje-li zadání na neexistující soubory (šablona, data, skript), krátce je hledej v projektu; když nejsou, vytvoř vlastní ukázkovou verzi ve formátu ze zadání a pokračuj.
- Ukládej do nové složky `web3d-<název>/` (pokud zadání neříká jinak) a nepřepisuj existující soubory.
- Na konci vypiš „Předpoklady“ – co sis domyslel nebo vytvořil náhradou.
- Ptát se smíš jen u nevratných kroků (mazání, přepis) nebo když zadání úplně chybí.

## Workflow

### 1. Brief (bez otázek – co chybí, rozhodni sám a zapiš jako předpoklad)
Ujasni si a napiš do komentáře na začátek souboru:
- **Předmět**: co stránka prodává/představuje (produkt, značka, služba, osobní projekt).
- **Jeden hlavní moment**: jaký objekt a co udělá (rozloží se na vrstvy, přelije se, reaguje na kurzor, roztříští se na částice…).
- **Pocit měřítka**: drží se v dlani (přesný, ostrý, malý) × velký jako budova (pomalý, zespodu, mlha) – viz art-direction.
- **Kam uložit**: jeden soubor `index.html` (výchozí) nebo projekt (Vite) – podle toho, co uživatel má.

### 2. Art direction (napiš jako tokeny do `:root` a komentář nad nimi)
- Paleta 4–6 barev odvozená z předmětu (ne výchozí fialovo-modrý gradient, pokud k tomu není důvod).
- Dvojice písem z Google Fonts: výrazné display + klidné body + mono pro HUD popisky.
- Rozvržení: kde je objekt, kde text, co je v rozích (HUD rámečky, čísla, stav).
- Jeden detail, který má jen tento předmět (jednotky, technické parametry, terminologie oboru) jako skutečný obsah.

### 3. Výběr techniky
Vyber z `references/techniques.md`:
- **Hero** (právě jedna): roj částic / morph, displacement blob, chromový nebo perleťový objekt, rozložené vrstvy (exploded view), světelné paprsky/warp, vlastní GLB model uživatele.
- **Interakce** (1–2): kurzor odpuzuje/naklání, scroll řídí kameru nebo rozložení, hover na hotspotech, klik přepíná stav.
- **Atmosféra** (0–2): bloom, film grain, chromatická aberace, mlha, prach, LED/CRT mřížka, scramble/glitch text.
Méně je víc: lepší jeden dokonalý efekt než pět průměrných.

### 4. Stavba
- Začni z `templates/starter.html` (jeden soubor, three.js přes importmap s **pevnou verzí** `three@0.160.0` z `cdn.jsdelivr.net/npm`). Pro Vite projekt: `npm i three@0.160.0`, stejný kód v modulech.
- Bez 3D modelu od uživatele stav objekty **procedurálně** (geometrie + shadery). Nikdy nestahuj cizí modely ani nepoužívej loga/značky, které uživatel nedodal.
- Hero objekt musí mít měřítko a světlo (environment map pro kovy, rim light, kontaktní stín nebo odraz). Kov bez prostředí vypadá jako plast.
- Text je HTML nad canvasem (přístupný, ostrý), 3D je pozadí/objekt. Žádný důležitý text jen v canvasu.
- Mobil od začátku: menší počet částic, DPR max 2 (na mobilu 1.5), objekt nad textem, žádné hover-only funkce.
- `prefers-reduced-motion`: zpomal/zastav animace, vypni auto-rotaci a kamerové lety.
- Fallback bez WebGL: statický gradient + text, stránka musí dávat smysl.
- Česky nebo jazykem uživatele; skutečný obsah, žádné lorem ipsum.

### 5. Kontrola (povinná, jednou)
- Zkopíruj `scripts/shoot.mjs` (ze složky tohoto skillu) do projektu a spusť tam `node shoot.mjs <cesta-k-html>` (Playwright musí být v projektu: `npm i -D playwright && npx playwright install chromium`; skript z jiné složky by balíček nenašel). Udělá snímky desktop 1440×900 a mobil 390×844 po 3 s a vypíše chyby z konzole.
- Prohlédni oba snímky. Oprav: prázdný/černý canvas, text přes objekt, ořezaný objekt na mobilu, nečitelný kontrast, chyby v konzoli. Pak hotovo – žádné nekonečné ladění.
- Pokud prohlížeč v prostředí nejde spustit, aspoň `node --check` na vytažený modulový skript a řekni uživateli, že vizuální kontrola neproběhla.

### 6. Předání
Krátce: co stránka dělá (hero + interakce), kde je soubor, jak ji spustit (`npx serve .` nebo otevřít soubor; importmap funguje i z `file://` v Chrome, jinak použít server) a 2–3 nápady na další krok.

## Pravidla kvality (kontrolní seznam před předáním)
- [ ] Jeden jasný hlavní moment, rozpoznatelný na prvním snímku bez interakce.
- [ ] Objekt má světlo, materiál a měřítko (ne plochá barva).
- [ ] Interakce je plynulá (lerp/damping), nic neskáče.
- [ ] Typografie má hierarchii, HUD popisky mono, nadpis display.
- [ ] Mobil: objekt celý viditelný, text čitelný, nic nepřetéká do strany.
- [ ] 60 fps na běžném notebooku: částice ≤ 30k desktop / 15k mobil, post-processing max 2 passy.
- [ ] Reduced motion + WebGL fallback + `touch-action` na canvasu.
- [ ] Pevné verze knihoven, žádné jiné externí zdroje než CDN a Google Fonts.
