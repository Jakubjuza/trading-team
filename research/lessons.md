# Poučení desku (reflexe)

Krátká, ověřená poučení z uzavřených papírových obchodů (`research/outcomes.jsonl`) a verdiktů (`research/verdicts.jsonl`).
Desk je čte před každým verdiktem (skill pro-analyza, krok 0). Zapisuje je journal-reviewer.

Pravidla zápisu:
- jedno poučení = jedna odrážka: **pravidlo** – důkaz (n obchodů, Ø R, data) – datum,
- poučení s n < 5 označ „(slabý důkaz)“; když ho další data vyvrátí, přesuň ho do „Vyvrácené“,
- max. 12 aktivních poučení – sluč podobná, nejslabší smaž.

## Aktivní

- Short signály z 2026-10-29 po přeprodaném pohybu (ETH donchian_1d, funding −45 % p.a., RSI 1D ~31; XRP pullback_1d, −6,7 % za 24 h, RSI 1D 34) – desk oba správně označil jako odrazové riziko a dal jen C (0,42 a 0,45, jen sledovat); oba papírové vstupy z 1H (mtf) skončily na stopu (ETH −1,202 R po 23 svíčkách, XRP −1,132 R po 101 svíčkách) – důkaz: n=2, Ø R −1,167, oba ve stejný den a na korelovaném trhu (téměř jedna sázka), oddělení nelze hodnotit (verdikty nemají `scores`) – 2026-11-03 (slabý důkaz)
- Verdikt C u shortu po −5 % a víc za 24 h (RSI 1D < 35) zatím sedí s výsledkem – důkaz: n=2 (ETH, XRP), obě ztráty, žádný zmeškaný zisk (NO_TRADE/C ziskový: 0) – 2026-11-03 (slabý důkaz)

## Vyvrácené

- (zatím žádná)

## Zpracované výsledky

Počet zpracovaných řádků z research/outcomes.jsonl: 2
