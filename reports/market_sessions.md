# Světové burzy a krypto (2026-11-19)

Hodinové svíčky 2024-11-21 – 2026-11-19, 8 mincí (BTC, ETH, SOL, XRP, ADA, LINK, AVAX, DOGE). Časy otevření v místním čase burzy (letní/zimní čas se počítá zvlášť pro každou zemi).

## Co se děje 4 hodiny po otevření

| Otevření | Pohyb vs. běžné 4 h | Rozpětí mezi mincemi | Ø směr | t-stat | P(růst) |
|---|---|---|---|---|---|
| Sydney (ASX) | 1.05× | 1.02–1.09× | -0.07 % | -1.0 | 48% |
| Tokio (TSE) | 1.07× | 1.01–1.13× | -0.02 % | -0.2 | 50% |
| Hongkong (HKEX) | 0.96× | 0.93–1.02× | +0.05 % | +0.8 | 50% |
| Londýn (LSE) | 0.95× | 0.92–0.99× | +0.09 % | +1.4 | 52% |
| New York (NYSE) | 1.44× | 1.29–1.67× | -0.02 % | -0.2 | 50% |
| CME (neděle) | 1.42× | 1.33–1.55× | -0.04 % | -0.1 | 54% |

Směr po otevření není u žádné burzy statisticky významný (|t| < 2). Otevření mění **volatilitu**, ne směr.

## CME gap

Cena se do 5 dnů vrátila na úroveň pátečního zavření CME v **77%** případů (gap ≥ 0,5 %, Ø velikost 3.6 %). Stejně vzdálená náhodná úroveň: 67%. Gap tedy cenu přitahuje mírně víc než jiná úroveň – vhodný jako cíl nebo magnet, ne jako jistota.

## Víkendový pohyb a nedělní otevření (CME + Asie)

| Víkend | 4 h po otevření: odraz | Ø pohyb | 24 h po otevření: odraz | Ø pohyb |
|---|---|---|---|---|
| propad ≥ 2 % | 57% | -0.11 % | 68% | +1.14 % |
| růst ≥ 2 % | 55% | -0.10 % | 55% | -0.83 % |

**Kontrola na 10 letech denních dat** (So+Ne → pondělí, 8 mincí):

- po víkendovém propadu ≥ 2 %: další den růst v 54% případů, Ø +0.33 % ± 0.42 (n=951)
- po jiném 2denním propadu ≥ 2 %: další den růst v 52% případů, Ø +0.10 % ± 0.16 (n=7186)
- po letech (víkendový propad → růst v pondělí): 2018: 40%, 2019: 58%, 2020: 58%, 2021: 53%, 2022: 49%, 2023: 37%, 2024: 48%, 2025: 56%, 2026: 71%

Závěr: za poslední 2 roky odraz po víkendovém propadu převažoval, ale na 10 letech je rozdíl proti jakémukoli jinému 2dennímu propadu malý a silně kolísá podle roku. Je to režimní jev, ne pravidlo – desk ho bere jako kontext s nízkou jistotou, ne jako signál.

## Kdy je trh živý (BTC, hodina UTC → násobek průměrné hodinové změny)

0:00 0.96× · 1:00 1.11× · 2:00 0.99× · 3:00 0.89× · 4:00 0.79× · 5:00 0.80× · 6:00 0.82× · 7:00 0.81× · 8:00 0.92× · 9:00 0.83× · 10:00 0.74× · 11:00 0.78× · 12:00 0.91× · 13:00 1.31× · 14:00 1.66× · 15:00 1.56× · 16:00 1.13× · 17:00 1.23× · 18:00 1.05× · 19:00 0.99× · 20:00 0.97× · 21:00 0.93× · 22:00 0.99× · 23:00 0.83×

## Jak to desk používá

- Datový list má sekci `sessions`: co je otevřené, co se otevírá v příštích 24 h s historickou volatilitou, aktuální CME gap.
- macro-analyst ji hodnotí, entry-exit-planner a devils-advocate řeší vstup těsně před otevřením New Yorku / CME (širší knoty).
- Telegram signál má v řádku 4 upozornění, když se do 6 h otevírá burza s ≥ 1,2× volatilitou, nebo je víkend.
- Do pravidel skeneru se otevírání burz zatím **nepřidává** – směrový efekt se neprokázal.

Nejde o finanční poradenství.
