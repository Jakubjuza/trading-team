# Pravděpodobnosti strategií (2026-10-29)

Po nákladech 0.15 % na stranu. P(T1) = cena došla na T1 dřív než na stop.

## donchian_1d (donchian_breakout, 1d)

Celkem 627 obchodů: P(T1) 32%, P(zisk) 51%, P(≥2R) 16%, Ø +0.40 R ± 0.13

Kalibrace na posledních 30 % (n=171): předpověď P(T1) 33% → skutečnost 29%; Ø R předpověď +0.46 → skutečnost +0.16; Brier 0.2106 (bez modelu 0.2044)

| Předpověď P(T1) | Obchodů | Ø předpověď | Skutečnost |
|---|---|---|---|
| 0%–35% | 135 | 31% | 29% |
| 35%–45% | 20 | 36% | 25% |
| 45%–55% | 16 | 50% | 31% |

| Režim (trend · volatilita · objem) | n | P(T1) | P(zisk) | Ø R |
|---|---|---|---|---|
| with · low · normal | 159 | 30% | 51% | +0.35 |
| with · mid · normal | 84 | 25% | 45% | +0.21 |
| with · low · high | 62 | 45% | 58% | +0.83 |
| neutral · mid · normal | 59 | 29% | 59% | +0.45 |
| with · mid · high | 56 | 32% | 45% | +0.26 |
| neutral · low · high | 52 | 36% | 54% | +0.38 |
| neutral · mid · high | 40 | 35% | 52% | +0.37 |
| neutral · low · normal | 33 | 39% | 52% | +0.69 |

## pullback_1d (pullback, 1d)

Celkem 646 obchodů: P(T1) 27%, P(zisk) 44%, P(≥2R) 15%, Ø +0.29 R ± 0.14

Kalibrace na posledních 30 % (n=220): předpověď P(T1) 29% → skutečnost 25%; Ø R předpověď +0.33 → skutečnost +0.14; Brier 0.1908 (bez modelu 0.1875)

| Předpověď P(T1) | Obchodů | Ø předpověď | Skutečnost |
|---|---|---|---|
| 0%–35% | 220 | 29% | 25% |

| Režim (trend · volatilita · objem) | n | P(T1) | P(zisk) | Ø R |
|---|---|---|---|---|
| with · low · normal | 288 | 31% | 45% | +0.36 |
| with · mid · normal | 208 | 27% | 42% | +0.20 |
| with · high · normal | 72 | 21% | 33% | -0.04 |
| with · low · high | 33 | 21% | 52% | +0.28 |
| with · mid · high | 30 | 30% | 50% | +0.99 |

