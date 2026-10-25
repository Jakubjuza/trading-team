# Pravděpodobnosti strategií (2026-10-25)

Po nákladech 0.15 % na stranu. P(T1) = cena došla na T1 dřív než na stop.

## brh_1h (breakout_retest_hold, 1h)

Celkem 955 obchodů: P(T1) 30%, P(zisk) 36%, P(≥2R) 19%, Ø +0.05 R ± 0.12

Kalibrace na posledních 30 % (n=255): předpověď P(T1) 30% → skutečnost 30%; Ø R předpověď +0.07 → skutečnost +0.01; Brier 0.2172 (bez modelu 0.2108)

| Předpověď P(T1) | Obchodů | Ø předpověď | Skutečnost |
|---|---|---|---|
| 0%–35% | 198 | 27% | 30% |
| 35%–45% | 57 | 37% | 32% |

| Režim (trend · volatilita · objem) | n | P(T1) | P(zisk) | Ø R |
|---|---|---|---|---|
| with · high · normal | 205 | 31% | 38% | +0.24 |
| with · mid · normal | 137 | 19% | 22% | -0.41 |
| with · high · high | 103 | 34% | 39% | +0.14 |
| neutral · mid · normal | 96 | 32% | 38% | +0.06 |
| neutral · high · normal | 93 | 23% | 30% | -0.23 |
| with · mid · high | 72 | 38% | 43% | +0.42 |
| with · low · normal | 60 | 33% | 38% | +0.23 |
| neutral · mid · high | 55 | 36% | 42% | +0.21 |
| neutral · low · normal | 43 | 33% | 37% | +0.04 |
| with · low · high | 39 | 23% | 26% | -0.40 |
| neutral · high · high | 32 | 28% | 38% | +0.24 |

## donchian_1d (donchian_breakout, 1d)

Celkem 697 obchodů: P(T1) 31%, P(zisk) 50%, P(≥2R) 16%, Ø +0.37 R ± 0.12

Kalibrace na posledních 30 % (n=196): předpověď P(T1) 32% → skutečnost 28%; Ø R předpověď +0.45 → skutečnost +0.16; Brier 0.2066 (bez modelu 0.2019)

| Předpověď P(T1) | Obchodů | Ø předpověď | Skutečnost |
|---|---|---|---|
| 0%–35% | 160 | 30% | 28% |
| 35%–45% | 20 | 37% | 30% |
| 45%–55% | 16 | 50% | 31% |

| Režim (trend · volatilita · objem) | n | P(T1) | P(zisk) | Ø R |
|---|---|---|---|---|
| with · low · normal | 159 | 30% | 51% | +0.35 |
| with · mid · normal | 82 | 26% | 45% | +0.19 |
| with · low · high | 62 | 45% | 58% | +0.83 |
| neutral · mid · normal | 59 | 30% | 59% | +0.45 |
| with · mid · high | 55 | 34% | 46% | +0.32 |
| with · high · normal | 53 | 28% | 40% | +0.02 |
| neutral · low · high | 52 | 36% | 54% | +0.38 |
| with · high · high | 49 | 24% | 39% | +0.26 |
| neutral · mid · high | 40 | 35% | 52% | +0.37 |
| neutral · low · normal | 32 | 41% | 53% | +0.75 |

## pullback_1d (pullback, 1d)

Celkem 707 obchodů: P(T1) 26%, P(zisk) 43%, P(≥2R) 15%, Ø +0.26 R ± 0.13

Kalibrace na posledních 30 % (n=238): předpověď P(T1) 29% → skutečnost 24%; Ø R předpověď +0.30 → skutečnost +0.10; Brier 0.1865 (bez modelu 0.1821)

| Předpověď P(T1) | Obchodů | Ø předpověď | Skutečnost |
|---|---|---|---|
| 0%–35% | 238 | 29% | 24% |

| Režim (trend · volatilita · objem) | n | P(T1) | P(zisk) | Ø R |
|---|---|---|---|---|
| with · low · normal | 286 | 30% | 44% | +0.36 |
| with · mid · normal | 189 | 26% | 42% | +0.14 |
| with · high · normal | 148 | 23% | 39% | +0.07 |
| with · low · high | 33 | 24% | 52% | +0.35 |

