# Katalog technik (three.js 0.160)

Importy (importmap viz `templates/starter.html`):
```js
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
```

Sdílený šum pro shadery (vlož do vertex shaderu, kde je potřeba):
```glsl
float hash(vec3 p){ p = fract(p * .3183099 + .1); p *= 17.; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float noise(vec3 x){
  vec3 i = floor(x), f = fract(x); f = f * f * (3. - 2. * f);
  return mix(mix(mix(hash(i), hash(i + vec3(1,0,0)), f.x), mix(hash(i + vec3(0,1,0)), hash(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(hash(i + vec3(0,0,1)), hash(i + vec3(1,0,1)), f.x), mix(hash(i + vec3(0,1,1)), hash(i + vec3(1,1,1)), f.x), f.y), f.z);
}
float fbm(vec3 p){ float a = .5, s = 0.; for (int i = 0; i < 4; i++){ s += a * noise(p); p *= 2.02; a *= .5; } return s; }
```

---

## HERO A · Roj částic a přelévání tvarů
Celá funkční ukázka: `templates/particle-morph.html`. Princip:
- Každý tvar = `Float32Array(N*3)` bodů (povrch koule – Fibonacci; torus; ellipsoid se závity = mozek; hrany+plochy krychle; text – vykresli text do 2D canvasu a vzorkuj neprůhledné pixely; obrázek/logo – totéž).
- Atributy `aFrom`, `aTo`, `aRnd`; uniform `uMorph` 0→1. Ve vertex shaderu `t = clamp(uMorph*1.45 - aRnd*.45, 0., 1.)` → každá tečka startuje jindy (vlna místo skoku), `sin(PI*t)` přidá vír uprostřed cesty.
- Při přepnutí uprostřed přechodu spočítej na CPU aktuální pozice a ulož je do `aFrom` (žádný skok).
- Body: `ShaderMaterial` + `AdditiveBlending` + `depthWrite:false`, velikost `uSize*uPix/-mv.z`, kulatý měkký bod ve fragmentu (`smoothstep(.5,.05,length(gl_PointCoord-.5))`).
- Kurzor: paprsek → průsečík s rovinou z=0 → `worldToLocal` → uniform `uMouse`; tečky v okruhu odsunout `normalize(p-uMouse)*f`.
- Barva podle výšky/šumu v 2–3 tónech; zesvětlit u kurzoru.
- „Tečkovaný povrch“ jako na Vesper videu: místo náhodných bodů použij pravidelnou mřížku na sféře (Fibonacci) a posouvej body podél normály `fbm(p*1.6 + uTime*.15)` – vznikne vlnící se tečkovaná slupka; díra uprostřed = torus místo sféry.

## HERO B · Displacement blob (organická hmota)
```js
const geo = new THREE.IcosahedronGeometry(1.4, 128);
const mat = new THREE.MeshPhysicalMaterial({ color:0x1a1f6b, metalness:.9, roughness:.18, clearcoat:1, clearcoatRoughness:.08, iridescence:1, iridescenceIOR:1.6, iridescenceThicknessRange:[120, 650] });
mat.onBeforeCompile = (sh) => {
  sh.uniforms.uTime = uTime; // { value:0 } sdílený objekt
  sh.vertexShader = 'uniform float uTime;\n' + NOISE_GLSL + sh.vertexShader.replace('#include <begin_vertex>', `
    float d = fbm(normal * 1.7 + uTime * .18) - .5;
    vec3 transformed = position + normal * d * .55;`);
};
```
Normály se po displacementu nepřepočítají – pro lesklé materiály je to obvykle v pořádku (odlesky „plavou“). Pro přesné normály použij `computeVertexNormals` na CPU jen u statické deformace.

## HERO C · Chromový / perleťový objekt (jako lesklá bunda)
Kov potřebuje prostředí, jinak je šedý:
```js
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), .04).texture;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.1;
const chrome = new THREE.MeshPhysicalMaterial({ color:0x2a35ff, metalness:1, roughness:.12, clearcoat:1, clearcoatRoughness:.05, iridescence:.6, iridescenceIOR:1.3 });
```
- Barevné odlesky: 2–3 `RectAreaLight` nebo silná `PointLight` v barvách palety mimo záběr, modrý key + teplý rim.
- **Prošívaný „puffer“ povrch procedurálně**: řada `CapsuleGeometry` (polštářky) vedle sebe, nebo `RoundedBoxGeometry` s displacementem `y += abs(sin(x*PI*k))*h` přes `onBeforeCompile` (švy = minima sinusu). Rukávy = zakřivené řady kapslí podél `CatmullRomCurve3`.
- Pozadí za objektem: tmavé, s jemnou mřížkou (LED/CRT overlay) a „ostnatými“ tahy (Canvas 2D textura s náhodnými lomenými čarami) – dává měřítko a styl streetwear.
- Model od uživatele: `GLTFLoader` + `DRACOLoader().setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/libs/draco/')`, po načtení přepiš materiály na `chrome` a vycentruj přes `Box3`.

## HERO D · Rozložené vrstvy (exploded view technologie)
```js
const layers = [];
const specs = [ ['Vnější plášť', 0x9aa4ff], ['Membrána', 0x6f7dff], ['Izolace', 0x7b4dff], ['Podšívka', 0xc9b8ff] ];
specs.forEach(([name, col], i) => {
  const m = new THREE.Mesh(new RoundedBoxGeometry(3, .14, 2.2, 4, .07),
    new THREE.MeshPhysicalMaterial({ color:col, metalness:.2, roughness:.35, transmission:.35, thickness:.5, transparent:true, opacity:.92 }));
  m.userData = { name, rest:i * .16, open:i * .75 }; group.add(m); layers.push(m);
});
// ve smyčce: p = vyhlazený scroll progress sekce (0..1)
layers.forEach(m => { m.position.y = THREE.MathUtils.lerp(m.userData.rest, m.userData.open, p); m.rotation.y = p * .35; });
```
- Jednu vrstvu udělej „datovou“: textura z Canvas 2D s čísly/kódem (scroll textury přes `map.offset.y += dt*.05`).
- Popisky vrstev = HTML hotspoty (viz Interakce C) s tenkou čarou k vrstvě.
- Prošívaná vrstva izolace: kapsle vedle sebe uvnitř vrstvy.

## HERO E · Světelné paprsky / warp (intro nebo přechod)
```js
const COUNT = 900, geo = new THREE.PlaneGeometry(.012, 1);
const mat = new THREE.ShaderMaterial({ transparent:true, depthWrite:false, blending:THREE.AdditiveBlending,
  uniforms:{ uTime:{ value:0 }, uSpeed:{ value:1 } },
  vertexShader:`attribute vec3 aOff; attribute float aLen; attribute vec3 aCol; uniform float uTime, uSpeed; varying vec3 vC; varying float vY;
    void main(){ vec3 p = position; p.y *= aLen * (1. + uSpeed * 2.); vY = position.y + .5;
      vec3 o = aOff; o.y = mod(aOff.y - uTime * (3. + aLen * 6.) * uSpeed, 20.) - 10.;
      vC = aCol; gl_Position = projectionMatrix * modelViewMatrix * vec4(p + o, 1.); }`,
  fragmentShader:`varying vec3 vC; varying float vY; void main(){ gl_FragColor = vec4(vC * vY, vY); }` });
const mesh = new THREE.InstancedMesh(geo, mat, COUNT); // aOff/aLen/aCol jako InstancedBufferAttribute
mesh.rotation.z = .35; // šikmý déšť jako na videu
```
Použij jako preloader (2–3 s, `uSpeed` 2→0) a pak přejdi na hlavní scénu; vodorovná linka dole = „horizont“.

## Interakce
**A · Kurzor naklání scénu:** `target = ndc*0.25; cur += (target-cur)*0.05; group.rotation.set(cur.y, cur.x, 0)`.
**B · Scroll řídí kameru/rozložení:** sekce mají výšku (např. 300vh) a `position:sticky` canvas; progress sekce = `(scrollY - top)/(height - innerHeight)` → vyhladit `p += (raw-p)*.08`. GSAP ScrollTrigger jen když je potřeba víc kroků (`https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js` + gsap.min.js).
**C · HTML hotspoty na 3D bodech:**
```js
const v = new THREE.Vector3(); obj.getWorldPosition(v); v.project(camera);
el.style.transform = `translate(${(v.x*.5+.5)*W}px, ${(-v.y*.5+.5)*H}px)`; el.hidden = v.z > 1;
```
**D · Magnetická tlačítka:** posun prvku o 25 % vzdálenosti kurzoru od středu, návrat pružinou.

## Atmosféra
**Bloom:** `new UnrealBloomPass(new THREE.Vector2(w,h), .7, .5, .75)` – práh vysoko, ať svítí jen světla a hrany.
**Grain + RGB posun (jeden ShaderPass):**
```js
const FX = { uniforms:{ tDiffuse:{ value:null }, uTime:{ value:0 }, uAmt:{ value:.0015 } },
  vertexShader:`varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.); }`,
  fragmentShader:`uniform sampler2D tDiffuse; uniform float uTime, uAmt; varying vec2 vUv;
    float r(vec2 c){ return fract(sin(dot(c, vec2(12.9898,78.233)) + uTime) * 43758.5453); }
    void main(){ vec2 d = (vUv - .5) * uAmt * 2.;
      vec3 c = vec3(texture2D(tDiffuse, vUv + d).r, texture2D(tDiffuse, vUv).g, texture2D(tDiffuse, vUv - d).b);
      c += (r(vUv) - .5) * .05; gl_FragColor = vec4(c, 1.); }` };
composer.addPass(new ShaderPass(FX)); // před OutputPass
```
**LED/CRT mřížka přes celou stránku (CSS):**
```css
.crt::after{content:"";position:fixed;inset:0;pointer-events:none;z-index:2;
  background:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px) 0 0/100% 3px,
             radial-gradient(circle at 1px 1px,rgba(255,255,255,.06) 1px,transparent 1.5px) 0 0/4px 4px;mix-blend-mode:overlay}
```
**Scramble / glitch text (nadpisy, menu):**
```js
function scramble(el, text, ms = 700){ const ch = '█▓▒░<>/\\|_-=+*#ABCDEFGHJKLMNPRSTUVXYZ0123456789'; const t0 = performance.now();
  (function f(){ const k = Math.min(1, (performance.now() - t0) / ms), n = Math.floor(k * text.length);
    el.textContent = text.slice(0, n) + [...text.slice(n)].map(c => c === ' ' ? ' ' : ch[Math.random() * ch.length | 0]).join('');
    if (k < 1) requestAnimationFrame(f); })(); }
```
Glitch vrstvy: `::before/::after` s `content:attr(data-text)`, posun ±2px, `clip-path: inset(...)` animovaný po krocích (`steps()`), jen krátce při hoveru nebo načtení.
**HUD rámečky:** rohové závorky z `border` na pseudo-elementech, mono popisky VELKÝMI s `letter-spacing:.12em`, drobná čísla (EST. 2024, 0.42 R, 24 000 částic) – vždy skutečná data stránky.

## Recepty kombinací (vyber podle předmětu)
- **Tech/AI služba:** HERO A (mozek/koule z teček) + kurzor A + grain. Světlé gradientové pozadí s tmavým objektem funguje taky.
- **Módní produkt:** HERO C (chrom/perleť) + HUD + LED mřížka + scramble menu + sekce HERO D „technologie“ na scroll.
- **Hardware/inženýrství:** HERO D (exploded) + hotspoty C + scroll B.
- **Studio/portfolio:** HERO E intro → HERO B blob + magnetická tlačítka.
- **Data/finance:** HERO A s tvarem grafu (body vzorkované z křivky ceny) + čísla v HUD.
