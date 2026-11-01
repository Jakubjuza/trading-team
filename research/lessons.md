# Poučení desku (reflexe)

Krátká, ověřená poučení z uzavřených papírových obchodů (`research/outcomes.jsonl`) a verdiktů (`research/verdicts.jsonl`).
Desk je čte před každým verdiktem (skill pro-analyza, krok 0). Zapisuje je journal-reviewer.

Pravidla zápisu:
- jedno poučení = jedna odrážka: **pravidlo** – důkaz (n obchodů, Ø R, data) – datum,
- poučení s n < 5 označ „(slabý důkaz)“; když ho další data vyvrátí, přesuň ho do „Vyvrácené“,
- max. 12 aktivních poučení – sluč podobná, nejslabší smaž.

## Aktivní

- Short donchian_1d při extrémně záporném fundingu (−45 % p.a.) a přeprodaném RSI 1D (~31) – desk to správně označil jako squeeze/odrazové riziko a dal jen C (jen sledovat); papírový vstup z 1H (mtf) skončil na stopu −1,2 R po 23 svíčkách – důkaz: n=1, R −1,202 (ETH, signál 2026-10-29, uzavřeno 2026-11-01); verdikt C 0,42 sedí s výsledkem, oddělení nelze hodnotit (verdikt nemá `scores`) – 2026-11-01 (slabý důkaz)

## Vyvrácené

- (zatím žádná)

## Zpracované výsledky

Počet zpracovaných řádků z research/outcomes.jsonl: 1
