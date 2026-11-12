# Pravděpodobnosti strategií (2026-11-12)

Po nákladech 0.15 % na stranu. P(T1) = cena došla na T1 dřív než na stop.

## donchian_1d (donchian_breakout, 1d)

Celkem 629 obchodů: P(T1) 32%, P(zisk) 51%, P(≥2R) 16%, Ø +0.39 R ± 0.12

Kalibrace na posledních 30 % (n=171): předpověď P(T1) 33% → skutečnost 26%; Ø R předpověď +0.47 → skutečnost +0.08; Brier 0.2041 (bez modelu 0.1939)

| Předpověď P(T1) | Obchodů | Ø předpověď | Skutečnost |
|---|---|---|---|
| 0%–35% | 138 | 31% | 27% |
| 35%–45% | 19 | 35% | 21% |
| 45%–55% | 14 | 51% | 29% |

| Režim (trend · volatilita · objem) | n | P(T1) | P(zisk) | Ø R |
|---|---|---|---|---|
| with · low · normal | 159 | 30% | 51% | +0.35 |
| with · mid · normal | 86 | 26% | 45% | +0.25 |
| neutral · mid · normal | 61 | 30% | 61% | +0.49 |
| with · low · high | 61 | 46% | 59% | +0.86 |
| with · mid · high | 56 | 30% | 43% | +0.16 |
| neutral · low · high | 53 | 36% | 53% | +0.36 |
| neutral · mid · high | 43 | 35% | 51% | +0.35 |
| neutral · low · normal | 32 | 41% | 53% | +0.75 |

## pullback_1d (pullback, 1d)

Celkem 650 obchodů: P(T1) 27%, P(zisk) 44%, P(≥2R) 15%, Ø +0.29 R ± 0.14

Kalibrace na posledních 30 % (n=222): předpověď P(T1) 30% → skutečnost 25%; Ø R předpověď +0.34 → skutečnost +0.12; Brier 0.1896 (bez modelu 0.1864)

| Předpověď P(T1) | Obchodů | Ø předpověď | Skutečnost |
|---|---|---|---|
| 0%–35% | 222 | 30% | 25% |

| Režim (trend · volatilita · objem) | n | P(T1) | P(zisk) | Ø R |
|---|---|---|---|---|
| with · low · normal | 290 | 31% | 45% | +0.37 |
| with · mid · normal | 209 | 27% | 42% | +0.19 |
| with · high · normal | 72 | 21% | 33% | -0.04 |
| with · low · high | 33 | 21% | 52% | +0.28 |
| with · mid · high | 31 | 29% | 48% | +0.92 |

