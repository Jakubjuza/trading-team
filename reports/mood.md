# 🌡️ Index nálady trhu – test na historii

Cenové složky indexu (trend, šíře trhu, volatilita, makro = 60 % vah) spočítané den po dni 2017-05-27 – 2026-10-25 (3439 dní), bez pohledu do budoucnosti. Fear & Greed, funding, stablecoiny a zprávy nemají dost dlouhou volně dostupnou historii, v testu chybí.

Otázka: vypovídá index o tom, co BTC udělá dál (7 / 30 / 90 dní)? Průměrný budoucí výnos BTC v % podle pásma indexu (v závorce počet dní):

| horizont | část | korelace | průměr | silně medvědí | medvědí | neutrální | býčí | silně býčí |
|---|---|---|---|---|---|---|---|---|
| 7 d | vše | +0.069 | +1.19 | +1.04 (331) | +0.31 (850) | +0.37 (952) | +2.54 (1041) | +1.80 (258) |
| 7 d | do 2021 | +0.081 | +1.92 | +4.04 (81) | +0.90 (423) | -0.06 (503) | +3.74 (545) | +3.92 (128) |
| 7 d | od 2022 | +0.041 | +0.49 | +0.07 (250) | -0.28 (427) | +0.86 (449) | +1.22 (496) | -0.29 (130) |
| 30 d | vše | +0.092 | +5.44 | +4.45 (331) | +2.21 (850) | +4.37 (949) | +9.48 (1021) | +5.30 (258) |
| 30 d | do 2021 | +0.116 | +8.64 | +15.96 (81) | +2.34 (423) | +4.91 (503) | +15.38 (545) | +10.81 (128) |
| 30 d | od 2022 | +0.029 | +2.33 | +0.72 (250) | +2.08 (427) | +3.76 (446) | +2.74 (476) | -0.13 (130) |
| 90 d | vše | +0.191 | +18.95 | +1.40 (331) | +9.37 (846) | +18.33 (927) | +30.69 (987) | +30.21 (258) |
| 90 d | do 2021 | +0.235 | +30.62 | +20.11 (81) | +6.07 (423) | +27.01 (503) | +51.21 (545) | +44.90 (128) |
| 90 d | od 2022 | +0.091 | +7.21 | -4.66 (250) | +12.67 (423) | +8.04 (424) | +5.38 (442) | +15.74 (130) |

Dní v pásmech: silně medvědí 331, medvědí 850, neutrální 959, býčí 1041, silně býčí 258.
Poslední hodnota cenových složek: 48.

## Závěr

Od roku 2022 (mimo vzorek) je korelace indexu s budoucím výnosem BTC na všech horizontech pod 0,1 a pásma nejsou seřazená (býčí pásmo nemá vyšší budoucí výnos než medvědí). Do roku 2021 index vypadal užitečněji, ale to bylo hlavně jedno velké býčí období. Překrývající se okna navíc přeceňují počet nezávislých pozorování.

**Index je popis nálady, ne signál.** Strategie, velikost pozic ani config se podle něj nemění.

AI úprava v týdenním reportu (události a geopolitika, max. ±10 bodů) se loguje do research/mood_ai.jsonl; po ≥ 26 týdnech mentor ověří, jestli k měřenému indexu něco přidává.
