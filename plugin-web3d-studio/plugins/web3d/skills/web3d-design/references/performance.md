# Výkon, mobil, přístupnost

## Rozpočty
| | Desktop | Mobil |
|---|---|---|
| Částice (Points) | ≤ 30 000 | ≤ 15 000 |
| Trojúhelníky scény | ≤ 500 000 | ≤ 150 000 |
| Post-processing | bloom + 1 ShaderPass | jen bloom nebo nic |
| devicePixelRatio | min(dpr, 2) | min(dpr, 1.5) |
| Textury | ≤ 2048 px | ≤ 1024 px |
| Světla se stíny | 1 | 0 (falešný kontaktní stín = průhledná textura) |

Mobil zjisti `Math.min(innerWidth, innerHeight) < 700 || matchMedia('(pointer: coarse)').matches`.

## Smyčka
- Jeden `requestAnimationFrame`, čas z `THREE.Clock`, pohyby násob `dt` (120Hz displeje).
- Pauza, když stránka není vidět: `document.visibilityState === 'hidden'` → nevykreslovat; canvas mimo viewport (IntersectionObserver) → nevykreslovat.
- Žádné alokace ve smyčce (`new Vector3` mimo smyčku).
- Morph/přepočty na CPU jen při události, ne každý snímek; jinak v shaderu.

## Odolnost
- WebGL fallback: `try { new WebGLRenderer() } catch` → statické pozadí a text zůstanou funkční.
- `renderer.setSize(w, h, false)` + CSS 100 % – žádné rozmazání ani přetečení.
- Canvas `touch-action: none` jen pokud stránka nemá scrollovat přes canvas; u scrollovaných stránek `pan-y`.
- Fonty: `document.fonts.ready` před kreslením textu do canvasu (jinak náhradní písmo v texturách).
- Pevné verze knihoven (`three@0.160.0`), žádné `@latest`.

## Přístupnost
- Veškerý obsah a navigace v HTML, canvas `aria-hidden="true"`.
- Viditelný focus na všech ovládacích prvcích, ovladatelné klávesnicí.
- `prefers-reduced-motion: reduce` → bez autorotace, introsekvence, glitch a scroll-jacku; morph zkrátit.
- Kontrast textu přes 3D ≥ 4.5:1 – pod text dej jemný gradient nebo sklo.
