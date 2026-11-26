# Vyhodnocení skeneru 2026-11-26 08:09 UTC

Náklady: poplatek 0.1 % + skluz 0.05 % na stranu (≈ 0.30 % ceny za celý obchod). Výsledky v R po nákladech.

## Odeslané signály (6)

- BTC/USDT 1h short 2026-10-24T16:00 (stop 0.21 %): stop, -2.44 R za 1 svíček
- ETH/USDT 1d short 2026-10-29T00:00 (stop 8.03 %): stop, -1.04 R za 6 svíček
- SOL/USDT 1d short 2026-10-29T00:00 (stop 8.68 %): time, +2.29 R za 20 svíček
- XRP/USDT 1d short 2026-10-29T00:00 (stop 13.56 %): time, +1.78 R za 20 svíček
- DOGE/USDT 1d short 2026-10-29T00:00 (stop 8.48 %): time, +2.27 R za 20 svíček
- SOL/USDT 1d short 2026-11-05T00:00 (stop 10.49 %): time, +1.99 R za 20 svíček

Uzavřené: {'n': 6, 'win': 66.7, 'avg_r': 0.808, 'ci': 1.626, 'sum_r': 4.85, 'max_dd_r': 1.04}

## Verdikty desku vs. výsledek

| Skupina | Uzavřené obchody | Win % | Ø R | Σ R |
|---|---|---|---|---|
| schváleno (A/B) | 0 | 0.0 | +0.000 | +0.00 |
| zamítnuto (C/NO_TRADE) | 6 | 66.7 | +0.808 | +4.85 |
| bez verdiktu | 0 | 0.0 | +0.000 | +0.00 |

Desk přidává hodnotu, jen když „schváleno (A/B)“ dlouhodobě vychází lépe než „zamítnuto“.

## Backtest aktuálního nastavení (BTC/USDT 17448 svíček, ETH/USDT 17445 svíček, SOL/USDT 17447 svíček, XRP/USDT 17448 svíček, ADA/USDT 17445 svíček, LINK/USDT 17445 svíček, AVAX/USDT 17445 svíček, DOGE/USDT 17446 svíček)

| | Obchody | Win % | Ø R (95% CI) | Σ R | Max DD (R) | Náhodné Ø R | Výhoda |
|---|---|---|---|---|---|---|---|
| BTC/USDT | 117 | 39.3 | -0.028 ± 0.275 | -3.3 | 14.76 | -0.275 | +0.247 |
| ETH/USDT | 116 | 39.7 | +0.098 ± 0.327 | +11.3 | 17.93 | -0.214 | +0.312 |
| SOL/USDT | 141 | 37.6 | +0.128 ± 0.314 | +18.0 | 15.96 | -0.170 | +0.298 |
| XRP/USDT | 113 | 37.2 | +0.033 ± 0.316 | +3.7 | 15.26 | -0.135 | +0.168 |
| ADA/USDT | 114 | 35.1 | +0.019 ± 0.345 | +2.1 | 20.4 | -0.144 | +0.163 |
| LINK/USDT | 99 | 38.4 | +0.103 ± 0.379 | +10.2 | 13.66 | -0.211 | +0.314 |
| AVAX/USDT | 115 | 34.8 | +0.187 ± 0.382 | +21.5 | 23.23 | -0.112 | +0.299 |
| DOGE/USDT | 125 | 28.8 | -0.018 ± 0.346 | -2.3 | 28.8 | -0.126 | +0.108 |
| **celkem** | 940 | 36.3 | +0.065 ± 0.118 | +61.3 | 98.88 | -0.173 | +0.238 |
| in-sample 70 % | 704 | 34.2 | +0.028 ± 0.139 | +19.8 | 83.3 | -0.133 | +0.161 |
| out-of-sample 30 % | 237 | 42.2 | +0.170 ± 0.226 | +40.2 | 20.78 | -0.225 | +0.395 |

## Strategie (celá historie, in-sample 70 % / out-of-sample 30 %)

| Strategie | Obchody | Ø R celkem | IS Ø R | OOS Ø R (95% CI) | Náhodné (OOS) |
|---|---|---|---|---|---|
| donchian_1d | 633 | +0.396 | +0.481 | +0.165 ± 0.205 | +0.076 |
| pullback_1d | 648 | +0.296 | +0.382 | +0.136 ± 0.199 | +0.069 |

## Uzavřené papírové obchody (research/outcomes.jsonl)

9 uzavřených, 5 v zisku, Σ +16,19 R, Ø +1,80 R (z toho 4 obchody se vstupem z nižšího TF „+mtf“; bez nich 5 obchodů, Σ +7,29 R). Vzorek je malý – o strategii nerozhoduje.

## Hypotéza H3 – `skip_weekends: true` (zvlášť pro každou denní strategii, jiné parametry beze změny)

Stejná metodika jako tabulka „Strategie“ (IS/OOS 70/30 na každé minci, náhodné vstupy, náklady z configu). Poloviny OOS = OOS obchody seřazené podle času a rozdělené na dvě stejné části.

| Strategie | Varianta | IS n | IS Ø R | OOS n | OOS Ø R (95% CI) | Náhodné (OOS) | OOS 1. pol. | OOS 2. pol. | Lepší mince (OOS) |
|---|---|---|---|---|---|---|---|---|---|
| donchian_1d | dnes | 463 | +0.481 | 170 | +0.165 ± 0.205 | +0.076 | −0.045 | +0.374 | |
| donchian_1d | skip_weekends | 405 | +0.466 | 148 | +0.268 ± 0.220 | +0.091 | +0.247 | +0.289 | 8/8 |
| pullback_1d | dnes | 430 | +0.382 | 219 | +0.136 ± 0.199 | +0.069 | +0.126 | +0.146 | |
| pullback_1d | skip_weekends | 388 | +0.360 | 196 | +0.200 ± 0.198 | +0.069 | +0.174 | +0.227 | 7/8 |

**Výsledek: neprošla.** Samotné kritérium hypotézy (OOS +≥ 0,05 R, ≥ 100 OOS obchodů, výhoda nad náhodou) je splněno u obou strategií, ale pravidla pro změnu configu ne: in-sample je horší u obou (−0,015 a −0,022 R) a u Donchianu je 2. polovina OOS horší (−0,085 R). Rozdíly jsou navíc hluboko uvnitř intervalů spolehlivosti. Config beze změny.

## Závěr kontroly

- Obě zapnuté strategie mají kladné OOS Ø R po nákladech a porážejí náhodné vstupy (donchian +0,165 vs. +0,076; pullback +0,136 vs. +0,069) → ponechat zapnuté. CI je ale široké (±0,2 R).
- Desk: všech 6 vyhodnocených signálů mělo verdikt C/NO_TRADE a 4 z nich skončily v zisku (Σ +4,85 R); A/B zatím 0 obchodů – přidanou hodnotu desku nelze posoudit (H12 čeká na ≥ 50 obchodů).
- Kalibrace scénářů (neutrální střed, roky 2022–2026): pod medvědím 11–12 %, nad mediánem 44–46 %, nad býčím 6–7 % – v pásmu ~10/50/10 %, býčí okraj mírně široký.
- Navržená změna: žádná.
