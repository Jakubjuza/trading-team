# Vstup na 15M při začínajícím uptrendu po propadu a panice (25. 10. 2026)

Předem stanovený test (`research/experiments/recovery.py`, GitHub Actions, 15M svíčky OKX s objemem, 8 mincí,
10/2024–10/2026). Kontext: ≥ 25 % propad za 30 dní, volatilita 4H byla v horních 10 % a teď je v dolní polovině,
na 1H rostoucí maxima i minima (fraktály), malé 15M svíčky. Vstup: 15M zavře nad posledním 1H maximem. Stop pod
posledním 1H minimem (min. 0,3 %). Max. 14 dní.

**60 vstupů** (19 na nízkém objemu, 41 na vysokém).

| Výstup (náklady 0,07 %) | Skupina | n | Úspěšnost | Ø R ± CI | Největší | Σ R | Náhoda Ø R |
|---|---|---|---|---|---|---|---|
| po +2R trailing | vše | 60 | 33 % | −0,04 ± 0,42 | +5,5 | −2,5 | −0,08 |
| | nízký objem | 19 | 21 % | −0,36 ± 0,62 | +3,0 | −6,9 | |
| | vysoký objem | 41 | 39 % | +0,11 ± 0,54 | +5,5 | +4,5 | |
| cíl 10R | vše | 60 | 7 % | −0,75 ± 0,40 | +9,6 | −45,3 | +0,03 |
| cíl 20R | vše | 60 | 5 % | −0,94 ± 0,20 | +4,3 | −56,2 | +0,10 |

Spotové náklady (0,15 %): trailing −0,14 R, cíle −0,86 / −1,04 R. Obě poloviny období stejné (trailing −0,04 / −0,04).
Výzva 100 USD: trailing skončil na 92 / 73 / 38 USD (riziko 2 / 5 / 10 %), cíle 10R a 20R při 5–10 % riziku → ztráta účtu
ve 100 % simulací; P(≥ 1 000 USD) 0 %.

## Závěr

❌ **Neprošlo.** S trailing výstupem je výsledek kolem nuly (stejně jako náhodný long), velké cíle 10–20R se skoro nikdy
netrefí (žádný obchod ≥ 10R). Varianta s **nízkým objemem**, o kterou šlo, je nejhorší (21 % úspěšnost, Ø −0,36 R).
Vysoký objem vyšel mírně kladně (+0,11 ± 0,54 R, n = 41) – v rámci náhody, jen poznámka, ne signál.
Začínající uptrend po krachu se na 15M často znovu láme; těsný stop pod 1H minimem ho nevydrží.

Nejde o finanční poradenství.
