// Kontrolní snímky 3D stránky: desktop + mobil, výpis chyb z konzole.
// Použití: node shoot.mjs <cesta-k-html | http-url> [výstupní-složka]
// Vyžaduje Playwright: npm i -D playwright && npx playwright install chromium
import { chromium } from 'playwright';
import { resolve } from 'node:path';
import { mkdirSync } from 'node:fs';

const target = process.argv[2];
if (!target) { console.error('Použití: node shoot.mjs <soubor.html | url> [složka]'); process.exit(1); }
const url = /^https?:/.test(target) ? target : 'file://' + resolve(target);
const out = resolve(process.argv[3] || 'shots');
mkdirSync(out, { recursive:true });

const browser = await chromium.launch({ args:['--use-gl=angle', '--enable-webgl', '--ignore-gpu-blocklist'] });
let problems = 0;
for (const [name, vp, mobile] of [['desktop', { width:1440, height:900 }, false], ['mobil', { width:390, height:844 }, true]]) {
  const page = await browser.newPage({ viewport:vp, deviceScaleFactor:mobile ? 2 : 1, isMobile:mobile, hasTouch:mobile });
  const errs = [];
  page.on('pageerror', e => errs.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  page.on('requestfailed', r => errs.push('request: ' + r.url() + ' ' + (r.failure()?.errorText || '')));
  await page.goto(url, { waitUntil:'load' });
  await page.waitForTimeout(3000);
  const file = `${out}/${name}.png`;
  await page.screenshot({ path:file });
  // je obraz prázdný? (rozptyl jasu snímku; WebGL canvas nejde číst přímo)
  const b64 = (await page.screenshot({ type:'png' })).toString('base64');
  const blank = await page.evaluate(async (src) => {
    const img = new Image(); img.src = 'data:image/png;base64,' + src; await img.decode();
    const t = document.createElement('canvas'); t.width = 64; t.height = 64;
    const g = t.getContext('2d'); g.drawImage(img, 0, 0, 64, 64);
    const d = g.getImageData(0, 0, 64, 64).data; let s = 0, v = 0;
    for (let i = 0; i < d.length; i += 4) { const l = d[i] + d[i + 1] + d[i + 2]; s += l; v += l * l; }
    const n = d.length / 4, mean = s / n;
    return v / n - mean * mean < 30 ? 'snímek je skoro jednobarevný (možná se 3D nevykreslilo)' : null;
  }, b64);
  const hscroll = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
  console.log(`\n[${name}] ${file}`);
  if (blank) { console.log('  ! ' + blank); problems++; }
  if (hscroll) { console.log('  ! stránka přetéká do strany'); problems++; }
  errs.forEach(e => { console.log('  ! ' + e); problems++; });
  if (!blank && !hscroll && !errs.length) console.log('  ok');
  await page.close();
}
await browser.close();
console.log(problems ? `\nNalezeno problémů: ${problems}` : '\nBez problémů. Prohlédni snímky.');
