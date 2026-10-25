# Knihovna setupů – ověření (říjen 2026)

Náklady 0,15 % na stranu (poplatek 0,10 % + skluz 0,05 %), výsledky v R **po nákladech**.
Ověření: výběr parametrů na prvních 70 % historie 4 coinů (BTC, ETH, SOL, XRP), kontrola na posledních 30 %
(out-of-sample) a na 5 coinech, které výběr neviděl (ADA, LINK, AVAX, DOGE, BNB), srovnání s náhodnými vstupy.
Data: 1h a 4h = 2 roky (yfinance), 1d = celá historie od 2015–2020 podle coinu. Nejde o finanční poradenství.

## Výsledek: co prošlo

| Strategie | Obchody (9 coinů) | Ø R | Náhodné vstupy | Výhoda | Long / Short | Roky v plusu |
|---|---|---|---|---|---|---|
| **donchian_1d** – průraz 20denního max/min ve směru EMA 200, stop 2 ATR, trailing 3 ATR po T1 | 808 | **+0,37 ± 0,11** | +0,10 | **+0,27** | +0,61 / +0,11 | všechny 2015–2026 |
| **pullback_1d** – trend (EMA 50 > 200, roste), návrat k EMA 20, obratová svíčka | 836 | **+0,27 ± 0,12** | +0,09 | **+0,18** | +0,40 / +0,14 | všechny 2015–2026 |
| **brh_1h** – breakout → retest → hold (už běžel) | 1 048 | +0,06 ± 0,12 | −0,17 | +0,22 | | viz scanner_improvements.md |

Citlivost na náklady (donchian / pullback): 0,07 % → +0,39 / +0,29 R · 0,30 % → +0,34 / +0,22 R. Denní strategie jsou na poplatky málo citlivé.

## Co NEprošlo (vypnuto)

| Setup | 1h (OOS / neviděné coiny) | 4h | 1d |
|---|---|---|---|
| pullback | −0,17 / −0,07 | −0,18 / +0,01 | **prošel** |
| sweep & reclaim | −0,13 / −0,16 | −0,18 / +0,12 | OOS +0,47, neviděné −0,05 (málo obchodů, nekonzistentní) |
| squeeze breakout | −0,17 / −0,11 | −0,42 / +0,03 | OOS −0,19 (málo obchodů) |
| Donchian breakout | −0,13 / −0,06 | −0,06 / +0,12 | **prošel** |
| range fade | málo obchodů, nekonzistentní | – | – |

Na 1h/4h krypto tyto setupy po poplatcích výhodu nemají; denní sledování trendu ano.

## Pravděpodobnosti

`scanner/probabilities.json` (generuje `scanner/calibrate.py`), detail v `reports/probabilities.md`.
Ve zprávě se ukazují **čísla celé strategie** (P(zisk), P(T1), P(≥2R), Ø R) a pro střízlivost i Ø R za posledních 30 %.
Jemnější dělení podle režimu trhu (trend, volatilita, objem) kalibraci na nových datech **nezlepšilo**, proto se nepoužívá.

## Očekávání (poslední 2 roky, 8 coinů, limity pozic, riziko 0,5 %)

| Strategie | Signálů / rok | Ø R |
|---|---|---|
| brh_1h | 188 | +0,08 |
| donchian_1d | 34 | +0,12 |
| pullback_1d | 44 | +0,08 |
| **celkem** | **≈ 5 týdně** | **+0,08** |

10 000 USD → 12 164 USD za 2 roky, max. propad −19 % (při 1 %: 14 235 USD, −35 %).
Poslední 2 roky jsou pro denní strategie slabší než dlouhodobý průměr – počítej spíš s tímto.
