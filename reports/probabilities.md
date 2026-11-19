# Pravděpodobnosti strategií (2026-11-19)

Po nákladech 0.15 % na stranu. P(T1) = cena došla na T1 dřív než na stop.

## donchian_1d (donchian_breakout, 1d)

Celkem 632 obchodů: P(T1) 32%, P(zisk) 51%, P(≥2R) 16%, Ø +0.39 R ± 0.12

Kalibrace na posledních 30 % (n=169): předpověď P(T1) 33% → skutečnost 28%; Ø R předpověď +0.46 → skutečnost +0.15; Brier 0.2088 (bez modelu 0.2034)

| Předpověď P(T1) | Obchodů | Ø předpověď | Skutečnost |
|---|---|---|---|
| 0%–35% | 154 | 31% | 28% |
| 45%–55% | 15 | 51% | 33% |

| Režim (trend · volatilita · objem) | n | P(T1) | P(zisk) | Ø R |
|---|---|---|---|---|
| with · low · normal | 159 | 30% | 51% | +0.35 |
| with · mid · normal | 86 | 26% | 45% | +0.25 |
| neutral · mid · normal | 62 | 27% | 60% | +0.46 |
| with · low · high | 62 | 47% | 60% | +0.89 |
| with · mid · high | 56 | 32% | 45% | +0.21 |
| neutral · low · high | 54 | 37% | 54% | +0.40 |
| neutral · mid · high | 42 | 36% | 52% | +0.39 |
| neutral · low · normal | 32 | 41% | 53% | +0.75 |

## pullback_1d (pullback, 1d)

Celkem 649 obchodů: P(T1) 28%, P(zisk) 44%, P(≥2R) 15%, Ø +0.30 R ± 0.14

Kalibrace na posledních 30 % (n=220): předpověď P(T1) 30% → skutečnost 25%; Ø R předpověď +0.34 → skutečnost +0.13; Brier 0.1906 (bez modelu 0.1875)

| Předpověď P(T1) | Obchodů | Ø předpověď | Skutečnost |
|---|---|---|---|
| 0%–35% | 220 | 30% | 25% |

| Režim (trend · volatilita · objem) | n | P(T1) | P(zisk) | Ø R |
|---|---|---|---|---|
| with · low · normal | 290 | 31% | 45% | +0.37 |
| with · mid · normal | 210 | 28% | 43% | +0.22 |
| with · high · normal | 71 | 20% | 32% | -0.08 |
| with · low · high | 33 | 21% | 52% | +0.28 |
| with · mid · high | 30 | 30% | 50% | +0.99 |

