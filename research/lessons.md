# Poučení desku (reflexe)

Krátká, ověřená poučení z uzavřených papírových obchodů (`research/outcomes.jsonl`) a verdiktů (`research/verdicts.jsonl`).
Desk je čte před každým verdiktem (skill pro-analyza, krok 0). Zapisuje je journal-reviewer.

Pravidla zápisu:
- jedno poučení = jedna odrážka: **pravidlo** – důkaz (n obchodů, Ø R, data) – datum,
- poučení s n < 5 označ „(slabý důkaz)“; když ho další data vyvrátí, přesuň ho do „Vyvrácené“,
- max. 12 aktivních poučení – sluč podobná, nejslabší smaž.

## Aktivní

- Short signály z 2026-10-29 po přeprodaném pohybu (ETH donchian_1d, funding −45 % p.a., RSI 1D ~31; XRP pullback_1d, −6,7 % za 24 h, RSI 1D 34; DOGE pullback_1d, F&G 30) – desk všechny tři označil jako odrazové riziko a dal C (ETH 0,42, XRP 0,45) resp. NO_TRADE (DOGE 0,41); všechny tři papírové vstupy z 1H (mtf) skončily na stopu (ETH −1,202 R po 23 svíčkách, XRP −1,132 R po 101, DOGE −1,141 R po 117) – důkaz: n=3, Ø R −1,158, všechny ve stejný den a na korelovaném trhu (téměř jedna sázka; verdikt DOGE sám zmiňuje „4. korelovaný alt short“) – 2026-11-04 (slabý důkaz)
- Verdikt C/NO_TRADE u shortu po −5 % a víc za 24 h (RSI 1D < 35) zatím sedí s výsledkem – důkaz: n=3 (ETH C, XRP C, DOGE NO_TRADE), všechny ztráty, žádný zmeškaný zisk (NO_TRADE/C ziskový: 0) – 2026-11-04 (slabý důkaz)
- Oddělení u DOGE shortu (jediný verdikt se `scores`): kvant −1 (Ø −0,028 R, n=59) měl pravdu; struktura, deriváty, zprávy, makro a sentiment (každé +1) se mýlily; události a orderflow 0 (orderflow upozornil na bid zeď 0,07472 těsně pod vstupem). Trend/makro/sentiment oddělení tedy po výprodeji nadhodnotila a kvant s upozorněním na asymetrii (T1 za podporami, P(T1) 25 %) stál na správné straně – důkaz: n=1, DOGE −1,141 R, hodnocení oddělení z jednoho obchodu – 2026-11-04 (slabý důkaz)
- Rozdíl mezi verdiktem a měřeným obchodem: verdikty hodnotí denní signál (stop 8,0 % ETH, 13,6 % XRP, 8,5 % DOGE od vstupu), kdežto papírové mtf obchody z 1H měly stopy 1,5 % (ETH), 2,3 % (XRP), 2,2 % (DOGE) – R:R a velikost z verdiktu se tedy nevztahují na obchod, který se měřil; při hodnocení oddělení k tomu přihlížet – důkaz: n=3, všechny 3 stopy, Ø R −1,158 – 2026-11-04 (slabý důkaz)

## Vyvrácené

- (zatím žádná)

## Zpracované výsledky

Počet zpracovaných řádků z research/outcomes.jsonl: 3
