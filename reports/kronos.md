# Kronos – předpověď další 2H svíčky (BTC, ETH, SOL)

Vygenerováno 2026-11-06 22:17 UTC skriptem `research/experiments/kronos_test.py` (pravidla stanovená předem jsou v jeho hlavičce).
Model Kronos-small ([arXiv 2508.02739](https://arxiv.org/abs/2508.02739), [GitHub](https://github.com/shiyu-coder/Kronos)), kontext 512 svíček, 5 vzorků.
Období 01. 09. 2025 – 06. 11. 2026, 15543 předpovědí. Náklady 0,30 % za obchod (0,15 % na stranu).

## Verdikt: **NEPROJDE**

## Směr další svíčky

| Skupina | Předpovědí | Kronos trefa | p (vs. 50 %) | Moment | Vždy nahoru | MAE vs. nulová předpověď | Medián velikosti předpovědi |
|---|---:|---:|---:|---:|---:|---:|---:|
| BTC | 5181 | 51,1 % | 0,065 | 47,8 % | 49,9 % | 1,287 | 0,21 % |
| ETH | 5181 | 52,8 % | 0,000 | 47,2 % | 50,6 % | 1,271 | 0,29 % |
| SOL | 5181 | 50,6 % | 0,202 | 47,4 % | 50,4 % | 1,244 | 0,33 % |
| Vše | 15543 | 51,5 % | 0,000 | 47,5 % | 50,3 % | 1,264 | 0,27 % |
| 1. polovina | 7770 | 51,2 % | 0,016 | 47,2 % | 50,7 % | 1,248 | 0,30 % |
| 2. polovina | 7773 | 51,7 % | 0,001 | 47,8 % | 49,9 % | 1,285 | 0,25 % |

MAE poměr < 1 znamená, že Kronos odhadne velikost pohybu přesněji než předpověď „cena se nezmění“.

## Obchodování podle předpovědi (1 svíčka, po nákladech)

| Skupina | Pravidlo | Obchodů | Ø hrubě | Ø čistě | t | Σ čistě | Výher | 95. perc. náhody |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| BTC | každá svíčka | 5181 | −0,002 % | −0,302 % | −33,64 | −1562,1 % | 23 % | −0,285 % |
| BTC | předpověď nad 0,30 % | 1896 | +0,019 % | −0,281 % | −16,65 | −533,2 % | 27 % | −0,269 % |
| ETH | každá svíčka | 5181 | +0,035 % | −0,265 % | −21,11 | −1375,5 % | 30 % | −0,278 % |
| ETH | předpověď nad 0,30 % | 2549 | +0,052 % | −0,248 % | −13,00 | −632,6 % | 32 % | −0,274 % |
| SOL | každá svíčka | 5181 | +0,019 % | −0,281 % | −20,35 | −1458,3 % | 33 % | −0,276 % |
| SOL | předpověď nad 0,30 % | 2814 | +0,024 % | −0,276 % | −13,70 | −777,0 % | 35 % | −0,268 % |
| Vše | každá svíčka | 15543 | +0,017 % | −0,283 % | −40,92 | −4396,0 % | 29 % | −0,288 % |
| Vše | předpověď nad 0,30 % | 7259 | +0,032 % | −0,268 % | −23,90 | −1942,7 % | 32 % | −0,282 % |
| 1. polovina | každá svíčka | 7770 | +0,022 % | −0,278 % | −25,39 | −2158,6 % | 31 % | −0,279 % |
| 1. polovina | předpověď nad 0,30 % | 3944 | +0,038 % | −0,262 % | −15,60 | −1031,7 % | 35 % | −0,270 % |
| 2. polovina | každá svíčka | 7773 | +0,012 % | −0,288 % | −34,05 | −2237,4 % | 27 % | −0,286 % |
| 2. polovina | předpověď nad 0,30 % | 3315 | +0,025 % | −0,275 % | −19,27 | −911,0 % | 29 % | −0,280 % |

Hodnoty v % jsou výnos na jeden obchod (ne R). Σ je prostý součet, bez skládání a bez páky.
Jen výzkum na historických datech; nejde o finanční poradenství.
