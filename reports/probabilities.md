# Pravděpodobnosti strategií (2026-11-02)

Po nákladech 0.15 % na stranu. P(T1) = cena došla na T1 dřív než na stop.

## donchian_1d (donchian_breakout, 1d)

Celkem 627 obchodů: P(T1) 32%, P(zisk) 51%, P(≥2R) 16%, Ø +0.40 R ± 0.13

Kalibrace na posledních 30 % (n=171): předpověď P(T1) 33% → skutečnost 28%; Ø R předpověď +0.46 → skutečnost +0.15; Brier 0.2097 (bez modelu 0.2019)

| Předpověď P(T1) | Obchodů | Ø předpověď | Skutečnost |
|---|---|---|---|
| 0%–35% | 136 | 31% | 29% |
| 35%–45% | 21 | 36% | 24% |
| 45%–55% | 14 | 51% | 29% |

| Režim (trend · volatilita · objem) | n | P(T1) | P(zisk) | Ø R |
|---|---|---|---|---|
| with · low · normal | 159 | 30% | 51% | +0.35 |
| with · mid · normal | 84 | 25% | 45% | +0.21 |
| with · low · high | 61 | 46% | 59% | +0.86 |
| neutral · mid · normal | 59 | 29% | 59% | +0.45 |
| with · mid · high | 57 | 32% | 46% | +0.26 |
| neutral · low · high | 52 | 36% | 54% | +0.38 |
| neutral · mid · high | 41 | 34% | 51% | +0.33 |
| neutral · low · normal | 32 | 41% | 53% | +0.75 |

## pullback_1d (pullback, 1d)

Celkem 647 obchodů: P(T1) 27%, P(zisk) 44%, P(≥2R) 15%, Ø +0.30 R ± 0.14

Kalibrace na posledních 30 % (n=220): předpověď P(T1) 29% → skutečnost 25%; Ø R předpověď +0.33 → skutečnost +0.15; Brier 0.1908 (bez modelu 0.1875)

| Předpověď P(T1) | Obchodů | Ø předpověď | Skutečnost |
|---|---|---|---|
| 0%–35% | 220 | 29% | 25% |

| Režim (trend · volatilita · objem) | n | P(T1) | P(zisk) | Ø R |
|---|---|---|---|---|
| with · low · normal | 288 | 31% | 45% | +0.36 |
| with · mid · normal | 209 | 27% | 43% | +0.23 |
| with · high · normal | 72 | 21% | 33% | -0.04 |
| with · low · high | 33 | 21% | 52% | +0.28 |
| with · mid · high | 30 | 30% | 50% | +0.99 |

