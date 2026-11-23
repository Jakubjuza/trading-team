# Scénáře na delších timeframech (2026-11-23)

Denní svíčky 8 mincí (BTC, ETH, SOL, XRP, ADA, LINK, AVAX, DOGE). Scénáře = percentily historických výnosů normovaných volatilitou, přenesené na dnešní volatilitu mince. Kalibrace: percentily jen z dat do konce roku 2021, porovnané se skutečností od roku 2022 (data, která model neviděl).

Jednorázový test (empirický střed, data do 2021 → od 2022):

| Horizont | Pod medvědím (cíl 10 %) | Nad mediánem (cíl 50 %) | Nad býčím (cíl 10 %) | V pásmu (cíl 80 %) | Dní testu |
|---|---|---|---|---|---|
| 4 týdny | 13 % | 41 % | 6 % | 81 % | 14072 |
| 13 týdnů | 19 % | 36 % | 5 % | 76 % | 13568 |
| 26 týdnů | 22 % | 29 % | 5 % | 73 % | 12840 |

**Kalibrace po letech 2022–2026** (každý rok jen z dat před ním) – dvě varianty středu:

| Varianta | Horizont | Pod medvědím (10 %) | Nad mediánem (50 %) | Nad býčím (10 %) | V pásmu (80 %) |
|---|---|---|---|---|---|
| empirický střed | 4 týdny | 12 % | 45 % | 7 % | 81 % |
| empirický střed | 13 týdnů | 14 % | 43 % | 7 % | 80 % |
| empirický střed | 26 týdnů | 16 % | 39 % | 6 % | 77 % |
| neutrální střed | 4 týdny | 12 % | 46 % | 7 % | 81 % |
| neutrální střed | 13 týdnů | 12 % | 45 % | 6 % | 81 % |
| neutrální střed | 26 týdnů | 11 % | 46 % | 7 % | 83 % |

Chyba kalibrace (součet odchylek od cílů, menší = lepší): empirický střed 0.452, neutrální střed 0.279. Skener používá: neutrální střed.

Směr podle režimu (týden nad/pod EMA21 × měsíc nad/pod SMA10) – P(růst) v datech do 2021 vs. od 2022:

| Horizont | Režim | Do 2021 | Od 2022 | Dní testu |
|---|---|---|---|---|
| 4 týdny | týden ↑ · měsíc ↑ | 55 % | 40 % | 4233 |
| 4 týdny | týden ↑ · měsíc ↓ | 54 % | 51 % | 1163 |
| 4 týdny | týden ↓ · měsíc ↑ | 55 % | 45 % | 1562 |
| 4 týdny | týden ↓ · měsíc ↓ | 61 % | 49 % | 7114 |
| 13 týdnů | týden ↑ · měsíc ↑ | 66 % | 41 % | 3941 |
| 13 týdnů | týden ↑ · měsíc ↓ | 49 % | 48 % | 1028 |
| 13 týdnů | týden ↓ · měsíc ↑ | 69 % | 46 % | 1534 |
| 13 týdnů | týden ↓ · měsíc ↓ | 56 % | 46 % | 7065 |
| 26 týdnů | týden ↑ · měsíc ↑ | 73 % | 42 % | 3941 |
| 26 týdnů | týden ↑ · měsíc ↓ | 66 % | 43 % | 1021 |
| 26 týdnů | týden ↓ · měsíc ↑ | 66 % | 54 % | 1534 |
| 26 týdnů | týden ↓ · měsíc ↓ | 65 % | 47 % | 6344 |

Čtení: rozpětí jsou použitelná, když skutečnost padá pod medvědí a nad býčí scénář zhruba v 10 % případů. Směr podle režimu se mezi obdobími neudržel (do 2021 býčí historie), proto ho desk nepoužívá jako pravděpodobnost. Okna se překrývají → nezávislých období je mnohem méně než dní.

Nejde o finanční poradenství.
