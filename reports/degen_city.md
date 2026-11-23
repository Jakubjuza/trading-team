# 🐸 Degen City – papírové město meme coinů

Samostatné město mimo desk. Vlastní kód (`degen/`) a vlastní workflow (`.github/workflows/degen.yml`). V Agentownu (https://claude.ai/artifact/HQXaGfrfq9XZhVcnFMmYi8) je to vlastní plovoucí ostrov **Degentown** bez mostu do ostatních čtvrtí (záložka Degentown, databáze `degen/state`). Záložní samostatná stránka: https://claude.ai/artifact/U3cHeroX6NrRWonhU31Zk6 (databáze `city/state`). Na skener, registr, riziko, demo účet ani peníze nesahá. Jen papír a upozornění na Telegram; nakupovat se dá jen ručně (např. přes vlastního Telegram bota).

Založeno 23. 11. 2026 na přání uživatele podle screenshotu „QuantumOrb / Solana bot“ (tvrzení +10 847 $ za 21 dní nejde ověřit, proto se tu všechno měří papírově a proti kontrolní skupině).

## Jak to běží

- GitHub Actions: jeden běh ~5,5 h, průchod každých ~30 s, na konci se sám znovu spustí; záloha cron každé 2 h. Stav v cache (`degen/cache/state.json`), malá záloha v gitu (`degen/persist.json`), přehled pro stránku `degen/city.json` (commit každých 15 min), uzavřené obchody `degen/trades.jsonl`.
- Agentown (kolekce `degen`, dokument `state`) se plní z `degen/city.json` naplánovanou úlohou (každou hodinu, celý soubor beze změn).
- Ostrov Degentown v Agentownu: kulatý bonbónový ostrov s kupolí (střed x 0, z 340, bez mostu), raketa na rampě, Měsíc, orb posledních 400 coinů (blíž středu = vyšší skóre, zelená 85+, červená veto), pět budov = pět účtů (výška podle stavu účtu) a pobíhající vlastní meme zvířátka (žabáci, kočky, pejsci, křečci, tučňáci s brýlemi, čepicemi a řetězy).
- Testovací běh: push na větev `claude/**` se změnou v `degen/` spustí 4minutový běh bez Telegramu.

## Zdroje dat

| zdroj | k čemu | klíč |
|---|---|---|
| pump.fun frontend API (neoficiální) | nově spuštěné coiny, tvůrce, sítě | ne |
| DexScreener `tokens/v1` | market cap, nákupy × prodeje 5 min, objem, likvidita, DEX (graduace) | ne |
| GeckoTerminal `new_pools` | záloha objevování a nové pooly po graduaci | ne |
| Solana RPC | první kupci, bundly, držitelé, financování peněženek | `HELIUS_API_KEY` (zdarma na helius.dev); bez něj veřejné RPC, 1 rozbor za průchod a limit 8 000 dotazů/den |

## Postup u každého coinu

1. **Předfiltr** (zdarma): věk 1,5–12 min, ≥ 12 nákupů za 5 min, nákupy ≥ prodeje, MC ≥ 6 000 $.
2. **On-chain rozbor** (~35 RPC dotazů): 25 nejstarších transakcí → první kupci, nákupy v bloku spuštění (bundly), nákup tvůrce; 10 největších držitelů bez bonding curve / poolu; u 5 prvních čerstvých kupců, kdo jim poslal SOL.
3. **Skóre 0–100** – 7 kanálů s pevnými vahami: tlak nákupů 20, tempo růstu 15, aktivita 10, rozptyl držitelů 20, bez bundlů 15, čistý tvůrce 10, sítě 10. Bez on-chain dat je skóre „neúplné“.
4. **Veto**: bundly ≥ 25 %, top 10 ≥ 40 %, ≥ 3 z 5 prvních kupců se stejným financovatelem, tvůrce financoval kupce, sériový tvůrce ≥ 5 coinů/24 h.

## Pět papírových účtů (1 000 $ každý)

| účet | budova | kdy kupuje |
|---|---|---|
| Filtr 85+ | 🔬 Laboratoř skóre | úplné skóre ≥ 85, bez veta, do 15 min |
| Kopírka peněženek | 🐋 Velrybí věž | mezi prvními kupci je chytrá peněženka (≥ 3 rané nákupy, ≥ 2 coiny 5× do 2 h, odhad úspěšnosti ≥ 50 %) |
| Graduace | 🎓 Univerzita | do 30 min po přechodu na PumpSwap/Raydium, likvidita ≥ 20 k$, nákupy ≥ 1,3× prodeje, objem 1 h ≥ 30 k$ |
| Shoda signálů | 🤝 Radnice | aspoň 2 ze 3 výše během 30 min |
| Kontrolní opice | 🐒 Klec | náhodný vzorek předfiltru (1 z 25) – měřítko |

Obchod: pozice 2 % účtu, max 8 najednou, vstup až na další ceně (~30 s zpoždění), poplatek 1,25 % na stranu + 0,40 $ za transakci + skluz podle likvidity. Výstupy: stop −40 %, ½ na +100 %, zbytek trailing 35 % od vrcholu (po prvním cíli nejhůř break-even), max 120 min; Graduace −30 % / +80 % / 30 % / 240 min. Bez cen 15 min → výstup za 30 % poslední ceny („bez dat“).

## Učení a kalibrace

- Každý rozebraný coin dostane štítek trojité bariéry (TP +100 % dřív než −40 %, SL naopak, TIME po 120 min). Stránka ukazuje podíl TP podle pásma skóre a sílu jednotlivých kanálů.
- Chytré peněženky se učí z výsledků: rané nákupy coinů, které do 2 h vystřelily ≥ 5×.
- **Váhy, prahy a pravidla se mění jen po testu na dostatečném vzorku**, nikdy podle rady nebo jednoho dne.

## Telegram

Signál Filtru, Kopírky, Graduace nebo Shody → zpráva s CA (ťuknutím zkopírovat), skóre, kanály a odkazy pump.fun / DexScreener / Solscan / Degen City; max 8 za hodinu. Denní přehled účtů v 19:00 UTC. Opice nic neposílá. Vypnutí: proměnná `DEGEN_TG=0` ve workflow.

## Známá omezení

- pump.fun API je neoficiální a může se změnit nebo blokovat; pak objevování jede přes GeckoTerminal.
- Papír neumí přesně simulovat frontrunning, MEV ani skutečný skluz v prvních sekundách; čísla budou spíš optimistická.
- Veřejné RPC stačí jen na málo rozborů; bez Helius klíče je většina skóre „neúplná“ a Filtr ani Kopírka skoro nenakupují.
