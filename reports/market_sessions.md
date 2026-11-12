# Světové burzy a krypto (2026-11-12)

Hodinové svíčky 2024-11-14 – 2026-11-12, 8 mincí (BTC, ETH, SOL, XRP, ADA, LINK, AVAX, DOGE). Časy otevření v místním čase burzy (letní/zimní čas se počítá zvlášť pro každou zemi).

## Co se děje 4 hodiny po otevření

| Otevření | Pohyb vs. běžné 4 h | Rozpětí mezi mincemi | Ø směr | t-stat | P(růst) |
|---|---|---|---|---|---|
| Sydney (ASX) | 1.06× | 1.03–1.09× | -0.09 % | -1.2 | 48% |
| Tokio (TSE) | 1.08× | 1.01–1.13× | -0.02 % | -0.3 | 50% |
| Hongkong (HKEX) | 0.96× | 0.93–1.01× | +0.04 % | +0.6 | 50% |
| Londýn (LSE) | 0.95× | 0.92–0.99× | +0.07 % | +1.1 | 51% |
| New York (NYSE) | 1.47× | 1.31–1.68× | -0.05 % | -0.5 | 49% |
| CME (neděle) | 1.49× | 1.42–1.63× | -0.07 % | -0.3 | 54% |

Směr po otevření není u žádné burzy statisticky významný (|t| < 2). Otevření mění **volatilitu**, ne směr.

## CME gap

Cena se do 5 dnů vrátila na úroveň pátečního zavření CME v **78%** případů (gap ≥ 0,5 %, Ø velikost 3.5 %). Stejně vzdálená náhodná úroveň: 67%. Gap tedy cenu přitahuje mírně víc než jiná úroveň – vhodný jako cíl nebo magnet, ne jako jistota.

## Víkendový pohyb a nedělní otevření (CME + Asie)

| Víkend | 4 h po otevření: odraz | Ø pohyb | 24 h po otevření: odraz | Ø pohyb |
|---|---|---|---|---|
| propad ≥ 2 % | 59% | -0.12 % | 71% | +1.45 % |
| růst ≥ 2 % | 55% | -0.04 % | 54% | -0.75 % |

**Kontrola na 10 letech denních dat** (So+Ne → pondělí, 8 mincí):

- po víkendovém propadu ≥ 2 %: další den růst v 54% případů, Ø +0.35 % ± 0.42 (n=944)
- po jiném 2denním propadu ≥ 2 %: další den růst v 52% případů, Ø +0.11 % ± 0.16 (n=7166)
- po letech (víkendový propad → růst v pondělí): 2018: 40%, 2019: 58%, 2020: 58%, 2021: 53%, 2022: 49%, 2023: 37%, 2024: 48%, 2025: 56%, 2026: 76%

Závěr: za poslední 2 roky odraz po víkendovém propadu převažoval, ale na 10 letech je rozdíl proti jakémukoli jinému 2dennímu propadu malý a silně kolísá podle roku. Je to režimní jev, ne pravidlo – desk ho bere jako kontext s nízkou jistotou, ne jako signál.

## Kdy je trh živý (BTC, hodina UTC → násobek průměrné hodinové změny)

0:00 0.97× · 1:00 1.10× · 2:00 0.97× · 3:00 0.87× · 4:00 0.79× · 5:00 0.79× · 6:00 0.82× · 7:00 0.83× · 8:00 0.91× · 9:00 0.83× · 10:00 0.73× · 11:00 0.78× · 12:00 0.91× · 13:00 1.32× · 14:00 1.64× · 15:00 1.57× · 16:00 1.14× · 17:00 1.23× · 18:00 1.06× · 19:00 0.99× · 20:00 0.98× · 21:00 0.93× · 22:00 0.99× · 23:00 0.84×

## Jak to desk používá

- Datový list má sekci `sessions`: co je otevřené, co se otevírá v příštích 24 h s historickou volatilitou, aktuální CME gap.
- macro-analyst ji hodnotí, entry-exit-planner a devils-advocate řeší vstup těsně před otevřením New Yorku / CME (širší knoty).
- Telegram signál má v řádku 4 upozornění, když se do 6 h otevírá burza s ≥ 1,2× volatilitou, nebo je víkend.
- Do pravidel skeneru se otevírání burz zatím **nepřidává** – směrový efekt se neprokázal.

Nejde o finanční poradenství.
