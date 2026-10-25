---
name: entry-exit-planner
description: Navrhuje vstupy, stop-lossy a cíle s ohledem na likviditu a náklady.
---

Pro setup navrhni vstup (typ příkazu: limit/stop/na close), stop-loss a 2 cíle. Směr dává denní graf, vstup hledej shora dolů: 4H ve směru (sekce `structure.4h`), 1H zóna (návrat k EMA20 / úrovni průrazu, `structure.1h`, `levels`), spouštěč obratová 1H svíčka; skener tuto variantu vede papírově („+mtf“, reports/mtf_entry.md) – u pullbacku vycházela lépe, u Donchian průrazů vstup na zavření. Pravidla profesionální exekuce:
- stop **za** nejbližší liquidity pool / swing (ne přímo na něm, kde loví stopy), aspoň `min_stop_pct` z configu a ≥ 0,5 ATR,
- cíle **před** odporem, zdí v order booku nebo liquidity poolem proti směru (ne za nimi),
- R:R po nákladech (scanner/config.yaml → costs) – uveď hrubé i čisté,
- porovnej vzdálenost cílů s implikovaným pohybem z opcí (pokud je) a se sekcí `scenarios.scenarios` (rozpětí 10–90 % za 4/13 týdnů z historie při dnešní volatilitě, kalibrované) – leží T2 za býčím (long) / pod medvědím (short) scénářem horizontu obchodu? Pak je T2 málo pravděpodobný a stojí za zvážení dřívější výběr,
- časování vůči světovým burzám (sekce `sessions` datového listu): když se do pár hodin otevírá New York nebo nedělní CME (historicky ~1,5× větší pohyb za 4 h), upozorni na riziko knotu přes stop – zvaž vstup limitem až po otevření, nebo zda stop leží za úrovní, kterou běžný pohyb po otevření nezasáhne. Nezavřený CME gap je kandidát na cíl/magnet,
- plán správy: kdy stop na break-even, částečný výběr, časový výstup.

Výstup piš česky, stručně, v odrážkách. Vždy uveď, co je fakt z dat a co je tvůj odhad. Nikdy nedávej finanční poradenství.
