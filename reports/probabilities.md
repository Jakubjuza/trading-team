# Pravděpodobnosti strategií (2026-11-09)

Po nákladech 0.15 % na stranu. P(T1) = cena došla na T1 dřív než na stop.

## donchian_1d (donchian_breakout, 1d)

Celkem 628 obchodů: P(T1) 32%, P(zisk) 51%, P(≥2R) 16%, Ø +0.40 R ± 0.13

Kalibrace na posledních 30 % (n=171): předpověď P(T1) 33% → skutečnost 28%; Ø R předpověď +0.48 → skutečnost +0.12; Brier 0.2079 (bez modelu 0.1993)

| Předpověď P(T1) | Obchodů | Ø předpověď | Skutečnost |
|---|---|---|---|
| 0%–35% | 137 | 31% | 28% |
| 35%–45% | 20 | 35% | 25% |
| 45%–55% | 14 | 51% | 29% |

| Režim (trend · volatilita · objem) | n | P(T1) | P(zisk) | Ø R |
|---|---|---|---|---|
| with · low · normal | 159 | 30% | 51% | +0.35 |
| with · mid · normal | 85 | 26% | 46% | +0.26 |
| with · low · high | 61 | 46% | 59% | +0.86 |
| neutral · mid · normal | 60 | 30% | 60% | +0.49 |
| with · mid · high | 57 | 32% | 44% | +0.24 |
| neutral · low · high | 53 | 36% | 53% | +0.36 |
| neutral · mid · high | 42 | 36% | 52% | +0.39 |
| neutral · low · normal | 32 | 41% | 53% | +0.75 |

## pullback_1d (pullback, 1d)

Celkem 648 obchodů: P(T1) 27%, P(zisk) 44%, P(≥2R) 15%, Ø +0.29 R ± 0.14

Kalibrace na posledních 30 % (n=220): předpověď P(T1) 30% → skutečnost 24%; Ø R předpověď +0.34 → skutečnost +0.12; Brier 0.1893 (bez modelu 0.1852)

| Předpověď P(T1) | Obchodů | Ø předpověď | Skutečnost |
|---|---|---|---|
| 0%–35% | 220 | 30% | 24% |

| Režim (trend · volatilita · objem) | n | P(T1) | P(zisk) | Ø R |
|---|---|---|---|---|
| with · low · normal | 288 | 31% | 45% | +0.36 |
| with · mid · normal | 208 | 27% | 42% | +0.20 |
| with · high · normal | 72 | 21% | 33% | -0.04 |
| with · low · high | 33 | 21% | 52% | +0.28 |
| with · mid · high | 32 | 31% | 50% | +1.00 |

