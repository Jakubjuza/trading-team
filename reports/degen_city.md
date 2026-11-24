# 🐸 Degen City – papírové město meme coinů

Samostatné město mimo desk. Vlastní kód (`degen/`) a vlastní workflow (`.github/workflows/degen.yml`). V Agentownu (https://claude.ai/artifact/HQXaGfrfq9XZhVcnFMmYi8) je to vlastní plovoucí ostrov **Degentown** bez mostu do ostatních čtvrtí (záložka Degentown, databáze `degen/state`). Na skener, registr, riziko, demo účet ani peníze nesahá. Jen papír a upozornění na Telegram; nakupovat se dá jen ručně (např. přes vlastního Telegram bota).

Založeno 23. 11. 2026 na přání uživatele podle screenshotu „QuantumOrb / Solana bot“ (tvrzení +10 847 $ za 21 dní nejde ověřit, proto se tu všechno měří papírově a proti kontrolní skupině).

## Jak to běží

- GitHub Actions: jeden běh ~5,5 h, průchod každých ~30 s, na konci se sám znovu spustí; záloha cron každé 2 h. Stav v cache (`degen/cache/state.json`), malá záloha v gitu (`degen/persist.json`), přehled pro stránku `degen/city.json` (commit každých 15 min), uzavřené obchody `degen/trades.jsonl`.
- Agentown (kolekce `degen`, dokument `state`) se plní z `degen/city.json` naplánovanou úlohou „Degentown – přenos dat do Agentownu“ (každou hodinu, celý soubor beze změn; notifikace jen když přepočet stojí 6 h).
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

## 🛡️ Bezpečnost před nákupem a 🔎 pitva pádů (23. 11. 2026, na přání uživatele)

**Proč to vzniklo**: první dva papírové obchody (SIIA −83 % za 30 s, Bra −56 % za 52 s) spadly hned po vstupu.

**Co platí o „vybrání likvidity“**
- Na pump.fun (bonding curve) likviditu vybrat nejde – SOL drží program; po graduaci na PumpSwap se LP tokeny pálí (RugCheck u obou coinů ukázal LP zamčené/spálené 100 %). Rychlý pád tam znamená, že tvůrce, bundly, snajpři nebo raní kupci prodali do křivky.
- Skutečné vybrání likvidity hrozí u coinů spuštěných přímo na Raydium/Meteora/Orca (Degentown je najde přes GeckoTerminal) s nezamčeným LP.
- „Nejde prodat“ = freeze authority nebo zrádná rozšíření Token-2022 (trvalý delegát, transfer hook, nepřevoditelný token, zmrazené účty, vysoký poplatek za převod).

**Tvrdé veto před každým papírovým nákupem** (`degen/safety.py`, ~2 RPC dotazy + RugCheck): mint authority aktivní, freeze authority aktivní, zrádná rozšíření Token-2022, poplatek za převod > 5 %, coin mimo pump.fun s LP zamčeným < 90 % nebo neověřitelným, tvůrce drží ≥ 10 %, tvůrce už dřív rugoval (RugCheck). Když mint nejde ověřit, nekupuje se. Kontrolní opice se kontroluje taky, ale kupuje dál (měří, kolik kontrola ušetří).

**Pitva** (`degen/postmortem.py`): po každém obchodu −30 % a horším a u rychlých pádů rozebraných coinů (max 12 za hodinu) se projde posledních ~30 transakcí → příčina: prodal tvůrce / raní kupci a bundly / jedna velryba / odliv kupců / vybraná likvidita (pokles likvidity poolu ≥ 80 % mimo pump.fun).

**Učení s pravidlem stanoveným předem**: každý rozebraný coin si uloží 11 znaků z okamžiku rozboru (dev ≥ 5 %, top 10 ≥ 25 %, bundly ≥ 10 %, ≥ 3 peněženky v bloku spuštění, společný financovatel, bez sítí, sériový tvůrce, převaha prodejů, rozbor < 3 min, MC < 8 k$, už 3× od startu). Po 30 min dostane štítek „rychlý pád“ (MC ≤ 30 % ceny při rozboru). Znak se stane **naučeným vetem**, když ho má ≥ 40 coinů a dolní mez 95% Wilsonova intervalu podílu pádů je o ≥ 10 bodů nad průměrem; zruší se, když to přestane platit. Každá změna jde na Telegram a do logu.

**Hypotéza k testu (zatím nezapnuto)**: „nečekat zbytečně dlouho“ – kratší časový stop (např. 30 min místo 120) a výstup, když tvůrce začne prodávat. Měří se přes pitvy a štítky; zapne se jen po testu.

## ⚙️ Motor v2 – papír už neumí „vydělat“ na vybrané likviditě (24. 11. 2026, upozornil uživatel)

**Co se stalo**: Graduace ukazovala ~2,1 mil. $ „realizováno“ z 1 000 $. Dva obchody (FIONA +7 978 722 %, 英伟达CEO +1 721 572 %) a CEO (+478 %) tvořily skoro celý zisk. Ověřeno 24. 11. (DexScreener + RugCheck z GitHub Actions): všechny tři coiny mají pool na PumpSwapu s **likviditou 0 $** a MC 5–42 $. Nešlo o coiny z pump.fun (mint nekončí „pump“) – pool založil někdo ručně a LP měl v rukou, takže ho mohl vybrat. Když likvidita zmizela, zbytkový pool ukázal nesmyslnou cenu (MC až 6,7 mld. $) a motor v1 „prodal“ za tuhle MC. Takový zisk nešel vybrat – uživatel měl pravdu.

**Chyby a opravy**
1. Motor v1 počítal prodej jako MC × počet tokenů s malým skluzem. Motor v2 (`degen/paper.py`) počítá nákup i prodej přes hloubku poolu (konstantní součin): víc, než je v poolu na straně SOL, vybrat nejde; u bonding curve se skutečné SOL dopočítá z virtuálních rezerv. Likvidita pod 500 $ nebo coin bez dat 15 min = pozice se počítá jako 0.
2. Velikost pozice: nejvýš 3 % quote strany poolu (v1 nechala složené úročení vrazit 50 000 $ do poolu s 20 000 $).
3. Hodnota účtu a otevřených pozic = kolik by šlo opravdu vybrat, ne MC.
4. Bezpečnost: pool na PumpSwapu se už nebere jako „pump.fun s spáleným LP“ – za bezpečný se považuje jen mint končící „pump“. Ručně založené pooly projdou kontrolou LP (zamčené/spálené ≥ 90 %, jinak veto; RugCheck „LP Unlocked“ = veto).
5. Graduace bere jen skutečné graduace z pump.fun (mint končí „pump“).

**Účty restartovány** 24. 11. na 1 000 $ (motor v2); souhrn v1 je v `archive` v city.json a na tabuli Degentownu. Staré řádky v `degen/trades.jsonl` nemají pole `engine` (v1), nové mají `engine: 2`.
