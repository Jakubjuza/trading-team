# Poučení desku (reflexe)

Krátká, ověřená poučení z uzavřených papírových obchodů (`research/outcomes.jsonl`) a verdiktů (`research/verdicts.jsonl`).
Desk je čte před každým verdiktem (skill pro-analyza, krok 0). Zapisuje je journal-reviewer.

Pravidla zápisu:
- jedno poučení = jedna odrážka: **pravidlo** – důkaz (n obchodů, Ø R, data) – datum,
- poučení s n < 5 označ „(slabý důkaz)“; když ho další data vyvrátí, přesuň ho do „Vyvrácené“,
- max. 12 aktivních poučení – sluč podobná, nejslabší smaž.

## Aktivní

- **Výsledky mtf obchodů (1H vstup, stop 1,5–2,3 %) nečíst jako důkaz pro ani proti dennímu verdiktu; poučení z nich nepoužívat v `lessons_used` denního signálu.** Verdikty hodnotí denní signál (stop 8,0–13,6 % od vstupu), mtf obchody mají jiné R:R, velikost i rozdělení výsledků: mtf n=5 (3× stop Ø −1,158 R; SOL 10-29 +12,376 R a SOL 11-05 +13,421 R, oba T1 a výstup časem po 480 barech; Ø +4,464 R, součet +22,322 R – výsledek stojí na dvou SOL obchodech) vs. denní n=5 (Ø +1,457 R). Mtf výsledek neodpovídá dennímu: u 4 ziskových denních signálů skončil mtf vstup 2× na stopu (XRP, DOGE 10-29) a 2× velkým ziskem (SOL 10-29, SOL 11-05); u ztrátového denního ETH 10-29 stop u obou. Chybu potvrdil SOL short 2026-11-05: NO_TRADE stál mj. na „ETH/XRP/DOGE shorty po přeprodání všechny na stopu“ (šlo o mtf obchody) a „kvant měl pravdu“ (jeden mtf obchod) – denní signál skončil časem 2026-11-25 na +1,981 R s T1 a mtf varianta téhož signálu (vstup 90,00, stop 91,35) 2026-11-27 na +13,421 R s T1 (verdicts.jsonl řádek 6, outcomes.jsonl řádky 9 a 10) – aktualizováno 2026-11-27 (n=5 mtf / 5 denních)
- **Desk dával C/NO_TRADE ziskovým denním shortům po přeprodaném pohybu (−5 % a víc za 24 h, RSI 1D < 35, F&G 28–30).** Denní shorty s C/NO_TRADE: SOL 10-29 C +2,294 R, XRP 10-29 C +1,782 R, DOGE 10-29 NO_TRADE +2,267 R, SOL 11-05 NO_TRADE +1,981 R (všechny T1, výstup časem po 20 barech), ETH 10-29 C −1,039 R (stop) – n=5, 4 ziskové, Ø +1,457 R, součet +7,285 R. Pozor: jen 2 dny signálu, všechny shorty v jednom medvědím pohybu 2026-10-29 až 2026-11-25 na korelovaném trhu, žádný jiný režim – 2026-11-26
- **Argumenty pro snížení stupně u denních shortů se nepotvrdily:** (a) T1 „pod 10. percentilem pásma / ambiciózní“ – SOL 10-29, XRP 10-29, SOL 11-05, T1 zasažen 3/3 (Ø +2,019 R); (b) bid zeď těsně pod vstupem (DOGE 0,07472 / 383 tis. USD, SOL 88,51 / 515 tis. USD) – T1 zasažen 2/2 (Ø +2,124 R); (c) statistika „odraz po víkendovém výprodeji“ (DOGE 65 %, n=29; SOL 73 %, n=22) – T1 zasažen 2/2. Čísla ve verdiktu nechat, ale nesnižovat jen kvůli nim stupeň – n=2–3 na argument, 4 různé obchody, Ø +2,081 R – 2026-11-26 (slabý důkaz)
- **Ve dvou verdiktech se skóre oddělení měla pravdu struktura, zprávy, makro a sentiment (+1 u obou), kvant a orderflow ne.** DOGE 10-29 (kvant −1, orderflow 0 s argumentem bid zdi) +2,267 R; SOL 11-05 (kvant 0, orderflow −1 kvůli bid zdi 88,51) +1,981 R; deriváty +1 / 0, události 0 / 0. Skóre oddělení má jen tyto 2 verdikty, oba ziskové shorty v témže trendu – n=2, Ø +2,124 R – 2026-11-26 (slabý důkaz)
- **Veto událostí jako časování (NFP/Fed) zatím stálo zisk, ne ztrátu.** SOL 11-05: veto „NFP pá 14:30 (~14 h) + jestřábí Fed“ → NO_TRADE, obchod skončil +1,981 R s T1. Riziko BOJ za 2,5 h uváděly všechny 4 verdikty z 10-29 (bez veta) – denní obchody 3 ze 4 ziskové. Případ, kdy veto ušetřilo ztrátu, v datech zatím není – n=1 veto – 2026-11-26 (slabý důkaz)

## Vyvrácené

- ~~Verdikt C/NO_TRADE u shortu po −5 % a víc za 24 h (RSI 1D < 35) sedí s výsledkem, žádný zmeškaný zisk~~ (zapsáno 2026-11-04, n=3 včetně mtf ztrát) – vyvráceno 2026-11-19: denní signály SOL (C), XRP (C) a DOGE (NO_TRADE) skončily +2,294 / +1,782 / +2,267 R s T1; z denních verdiktů C/NO_TRADE byla ztrátová jen ETH (−1,039 R). Znovu vyvráceno 2026-11-26: SOL 11-05 NO_TRADE +1,981 R s T1.
- ~~U DOGE shortu měl kvant (−1) pravdu, struktura/deriváty/zprávy/makro/sentiment (+1) se mýlily; trend/makro/sentiment po výprodeji nadhodnocují~~ (zapsáno 2026-11-04, n=1 mtf obchod −1,141 R) – vyvráceno 2026-11-19: denní DOGE signál skončil +2,267 R s T1; podruhé 2026-11-26: SOL 11-05 (struktura/zprávy/makro/sentiment +1, kvant 0, orderflow −1) skončil +1,981 R s T1 – n=2 verdikty se `scores`, oba proti tomuto tvrzení.
- ~~Poučení z ztrát mtf obchodů se propsalo do verdiktu SOL 11-05, výsledek zatím není~~ (zapsáno 2026-11-19) – uzavřeno 2026-11-26: výsledek je +1,981 R s T1; sloučeno do prvního aktivního poučení.

## Zpracované výsledky

Počet zpracovaných řádků z research/outcomes.jsonl: 10
