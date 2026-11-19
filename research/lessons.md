# Poučení desku (reflexe)

Krátká, ověřená poučení z uzavřených papírových obchodů (`research/outcomes.jsonl`) a verdiktů (`research/verdicts.jsonl`).
Desk je čte před každým verdiktem (skill pro-analyza, krok 0). Zapisuje je journal-reviewer.

Pravidla zápisu:
- jedno poučení = jedna odrážka: **pravidlo** – důkaz (n obchodů, Ø R, data) – datum,
- poučení s n < 5 označ „(slabý důkaz)“; když ho další data vyvrátí, přesuň ho do „Vyvrácené“,
- max. 12 aktivních poučení – sluč podobná, nejslabší smaž.

## Aktivní

- Shorty z 2026-10-29 po přeprodaném pohybu (−5 % a víc za 24 h, RSI 1D < 35, F&G 30): rozhodla šířka stopu, ne směr. Papírové vstupy z 1H (mtf) se stopem 1,5–2,3 % skončily všechny na stopu (ETH −1,202 R, XRP −1,132 R, DOGE −1,141 R; n=3, Ø −1,158 R), kdežto denní signály se stopem z verdiktu (8,0–13,6 %) vyšly 3 ze 4 se ziskem a T1 (SOL +2,294 R, XRP +1,782 R, DOGE +2,267 R, všechny ukončené časem po 20 denních svíčkách 2026-11-18; ETH −1,039 R na stopu) – důkaz: denní n=4, Ø +1,326 R; u XRP a DOGE stejný signál ztratil z 1H a vydělal z 1D; všech 7 obchodů je jeden den na korelovaném trhu (téměř jedna sázka) – 2026-11-19 (slabý důkaz)
- Rozdíl mezi verdiktem a měřeným obchodem: verdikty hodnotí denní signál (stop 8,0 % ETH, 8,7 % SOL, 13,6 % XRP, 8,5 % DOGE od vstupu), kdežto mtf obchody z 1H mají stopy 1,5–2,3 % – R:R, velikost i stupeň verdiktu se k mtf obchodu nevztahují a ztráty mtf obchodů nelze použít jako důkaz proti dennímu signálu – důkaz: n=3 mtf (Ø −1,158 R) vs. n=4 denní (Ø +1,326 R) na stejných signálech – 2026-11-19 (slabý důkaz)
- Desk dal C/NO_TRADE ziskovým denním shortům: ze 4 denních shortů z 2026-10-29 s verdiktem C/NO_TRADE byly 3 ziskové (SOL C +2,294 R, XRP C +1,782 R, DOGE NO_TRADE +2,267 R) a 1 ztrátový (ETH C −1,039 R). Argumenty pro snížení stupně (odraz po přeprodání, T1 „pod 10. percentilem pásma / ambiciózní“, bid zeď 0,07472 u DOGE) se v těchto 3 případech nepotvrdily – T1 byl zasažen u všech tří – důkaz: n=4, Ø +1,326 R, zmeškaný zisk u 3 z 4 – 2026-11-19 (slabý důkaz)
- Poučení z ztrát mtf obchodů se už propsalo do verdiktu: SOL short 2026-11-05 dostal NO_TRADE mj. s odkazem na „ETH/XRP/DOGE shorty po přeprodání všechny na stopu“ a „kvant měl pravdu“ – obě tvrzení stála na 1H obchodech a jednom obchodu a nyní jsou vyvrácená (viz níže); výsledek tohoto signálu zatím v outcomes není – důkaz: n=1 verdikt (research/verdicts.jsonl, řádek 6) – 2026-11-19 (slabý důkaz)

## Vyvrácené

- ~~Verdikt C/NO_TRADE u shortu po −5 % a víc za 24 h (RSI 1D < 35) sedí s výsledkem, žádný zmeškaný zisk~~ (zapsáno 2026-11-04, n=3 včetně mtf ztrát) – vyvráceno 2026-11-19: denní signály SOL (C), XRP (C) a DOGE (NO_TRADE) skončily +2,294 / +1,782 / +2,267 R s T1; z denních verdiktů C/NO_TRADE byla ztrátová jen ETH (−1,039 R).
- ~~U DOGE shortu měl kvant (−1) pravdu, struktura/deriváty/zprávy/makro/sentiment (+1) se mýlily; trend/makro/sentiment po výprodeji nadhodnocují~~ (zapsáno 2026-11-04, n=1 mtf obchod −1,141 R) – vyvráceno 2026-11-19: denní DOGE signál, který verdikt hodnotil, skončil +2,267 R s T1, takže na denním horizontu měla pravdu oddělení s +1 a kvant (−1) i orderflow (bid zeď 0,07472 pod vstupem) se mýlily; stále jen n=1 obchod se `scores`.

## Zpracované výsledky

Počet zpracovaných řádků z research/outcomes.jsonl: 7
