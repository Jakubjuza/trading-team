# web3d-studio · plugin pro Claude Code

Příkaz `/web3d` postaví kvalitní 3D webovou stránku v three.js: roje částic a přelévání tvarů, chromové a perleťové objekty, rozložené vrstvy produktu, světelné paprsky, glitch typografii a HUD rozhraní. Součástí je kontrola snímky na desktopu i mobilu.

## Instalace
1. Rozbal složku `web3d-studio` kamkoli (např. `~/claude-plugins/web3d-studio`).
2. V Claude Code:
   ```
   /plugin marketplace add ~/claude-plugins/web3d-studio
   /plugin install web3d@web3d-studio
   ```
3. Restartuj Claude Code.

Případně nahraj složku do GitHub repozitáře a přidej ho přes `/plugin marketplace add <uživatel>/<repo>`.

## Použití
```
/web3d landing page pro značku zimních bund, lesklá modrá bunda jako hero, streetwear HUD styl
/web3d úvodní stránka AI služby, mozek z částic, který reaguje na kurzor, světlé gradientové pozadí
/web3d produktová stránka sluchátek, rozložené vrstvy při scrollu s popisky
```
Pokud příkaz koliduje s jiným pluginem, použij `/web3d:web3d`. Skill `web3d-design` se spustí i sám, když napíšeš „udělej 3D web…“.

## Obsah
- `plugins/web3d/commands/web3d.md` – příkaz `/web3d`
- `plugins/web3d/skills/web3d-design/SKILL.md` – postup práce a kontrolní seznam kvality
- `references/techniques.md` – katalog technik s kódem (částice, blob, chrom, exploded view, warp, interakce, post-processing, glitch)
- `references/art-direction.md` – měřítko, světlo, typografie, palety, HUD, čemu se vyhnout
- `references/performance.md` – rozpočty pro desktop a mobil, přístupnost
- `templates/starter.html` – kostra stránky (perleťový blob, bloom, grain, HUD, scroll, kurzor)
- `templates/particle-morph.html` – roj částic přelévající se mezi tvary
- `scripts/shoot.mjs` – snímky desktop + mobil a výpis chyb (`npm i -D playwright && npx playwright install chromium`)
