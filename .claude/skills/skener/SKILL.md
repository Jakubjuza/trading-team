---
name: skener
description: Projde watchlist, najde obchodní příležitosti podle pravidel ve watchlist.md a upozorní uživatele jen na ty, které projdou filtrem. Použij, když uživatel napíše „skener“, nebo ho spustí naplánovaná úloha.
---

# Skener příležitostí

Pravidla a tickery: `.claude/skills/skener/watchlist.md`. Log upozornění: `reports/alerts.md`.

## 1. Rychlé síto (levné)

Spusť **chart-scanner** na celý watchlist: aktuální cena a svíčky přes yfinance (zdroj: Yahoo Finance; když nejde, web search se zdrojem), trend 4H/denní, nejbližší úrovně, a u každého tickeru „kandidát ano/ne + možný setup a spouštěč“. Kandidát = cena do max. vzdálenosti od spouštěče z watchlistu a setup povoleného typu.

Vyřaď kandidáty, kteří už jsou v `watcher/levels.json` (pravidlo duplicity ve watchlistu). Nech max. N nejlepších (watchlist).

Žádný kandidát → ponech platné setupy v `watcher/levels.json` (prošlé odstraň) a pokračuj krokem 5 s výsledkem „bez nových setupů“.

## 2. Plná analýza kandidátů

Pro každého kandidáta skill `pro-analyza` (datový list, oddělení desku, head-trader). Agentům předej pravidla z watchlistu (směr, typy setupů, účet, riziko, min. R:R, náklady).

## 3. Filtr

Do hlídání (krok 4) jde jen setup, který splní VŠE:
- devils-advocate nedal „zamítnout“, kvalita ≥ minimum z watchlistu,
- vážené R:R po nákladech ≥ minimum,
- spouštěč je do max. vzdálenosti od aktuální ceny (watchlist),
- spouštěč jde vyjádřit jedním z typů hlídače (níže).

## 4. Hlídané úrovně → `watcher/levels.json`

Upozornění na mobil posílá **Telegram hlídač** (`.github/workflows/watcher.yml`, každých 15 min, bez AI). Skener mu jen zapíše plán:

1. Načti `watcher/levels.json`. Odstraň setupy s prošlým `valid_until`. Setup na stejný ticker + směr nahraď novým, pokud nová analýza změnila úrovně; jinak ho ponech.
2. Přidej setupy, které prošly filtrem. Každý dostane nové `id` (`TICKER-SMER-YYYYMMDD-HHMM`, nikdy znovu nepoužívat; hlídač podle id pozná, co už oznámil).
3. Ke každému nechej chart-renderer nakreslit graf `reports/<TICKER>_<YYYY-MM-DD>_<HHMM>.png` a cestu dej do `chart`.

```json
{
  "updated": "2026-10-24T15:40:00+02:00",
  "setups": [{
    "id": "BTC-LONG-20261024-1540",
    "ticker": "BTC", "yf_symbol": "BTC-USD", "direction": "long",
    "setup": "retest 80k", "quality": "B",
    "trigger": {"type": "retest_long", "level": 80000, "timeframe": "1h", "tolerance_pct": 0.3,
                "min_volume_x": 1.5, "text": "1H svíčka se dotkne 80 000 a zavře nad"},
    "entry": 80050, "stop": 79150,
    "targets": [{"label": "T1", "price": 81300}, {"label": "T2", "price": 82250}],
    "rr": "2,1", "size": "0,09 BTC ≈ 7,3k USD, riziko 100 USD", "risk": "FOMC 28. 10.",
    "valid_until": "2026-10-26T20:00:00+01:00",
    "chart": "reports/BTC_2026-10-24_1540.png"
  }]
}
```

Typy spouštěče (vyhodnocuje se poslední **uzavřená** svíčka `timeframe` = `15m` / `1h` / `4h` / `1d`):
- `close_above` / `close_below` – close nad / pod `level` (breakout / breakdown),
- `retest_long` – low se dotkne `level` (± `tolerance_pct`) a close je nad ním,
- `retest_short` – high se dotkne `level` a close je pod ním,
- `min_volume_x` (volitelné) – objem svíčky ≥ násobek průměru 20 předchozích.

Hlídač sám zneplatní setup, když close projde stopem dřív, než se spustí. `valid_until` nastav realisticky (obvykle 24–72 h, nikdy přes velkou událost, kterou tým označil za zneplatňující).

## 5. Záznam a commit

Do `reports/alerts.md` přidej řádek za každé spuštění (i prázdné):
`| datum čas (Praha) | ticker | směr | setup | spouštěč | vstup | stop | T1/T2 | R:R | do hlídání ano/ne | důvod |`

Commitni `watcher/levels.json` a `reports/` a pushni do `main` (`git pull --rebase origin main` před pushem). Když push selže, zkus to jednou znovu; pak to uveď jedním řádkem v poslední zprávě.

## 6. Poslední zpráva

Notifikace **neposílej** (PushNotification nepoužívej) – nové setupy oznámí na Telegram hlídač při dalším běhu. Poslední zpráva max. 3 řádky, např.:
„Skener: 1 nový hlídaný setup (BTC long retest 80k, R:R 2,1). Hlídá se: 2 setupy.“ nebo „Skener: bez nových setupů (BTC, ETH, SOL, XRP). Hlídá se: 0.“
