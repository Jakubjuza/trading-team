---
name: chart-report
description: Z výsledku analýzy (ticker, vstup, stop-loss, cíle, range, scénáře z time-machine) nakreslí PNG graf se svíčkami do složky reports/. Použij jako poslední krok analýzy nebo když uživatel chce graf setupu.
argument-hint: (výsledek analýzy z konverzace) [cesta k CSV]
---

# Chart report

Skript: `.claude/skills/chart-report/render_chart.py` (Python, mplfinance + matplotlib).

## 1. Závislosti

Pokud `python3 -c "import mplfinance, yfinance"` selže: `pip install -q matplotlib mplfinance yfinance`.

## 2. Spec JSON

Ze závěru analýzy sestav `reports/<TICKER>_<YYYY-MM-DD>.json` (datum = den analýzy):

```json
{
  "ticker": "AAPL",
  "yf_symbol": "AAPL",
  "direction": "long",
  "title": "AAPL – long breakout nad ATH (setup A)",
  "bars": 60, "interval": "1d", "period": "6mo", "horizon_bars": 8, "decimals": 2,
  "entry": 352.5, "stop": 347.9,
  "targets": [{"label": "T1", "price": 360.4}, {"label": "T2", "price": 365.5}],
  "range": {"low": 339.5, "high": 348.15, "label": "Range", "high_label": "Range high"},
  "scenarios": [
    {"kind": "optimistic", "prob": "16 %", "path": [[2, 353], [5, 360.4], [7, 365.5]], "text": "Close nad ATH na objemu, T1 i T2."},
    {"kind": "neutral", "prob": "9 %", "path": [[3, 351], [7, 353]], "text": "Boční pohyb, časový výstup."},
    {"kind": "bad", "prob": "49 %", "path": [[2, 350], [4, 347.5]], "text": "Falešný breakout, stop."}
  ],
  "caption": "Krátký český popisek: setup, vstup/stop/cíle, R:R a hlavní riziko.",
  "data_source": "yfinance AAPL 1d"
}
```

- `path` = body `[počet svíček za poslední svíčkou, cena]`; trajektorie začíná na posledním close.
- Vždy právě 3 scénáře: `optimistic`, `neutral`, `bad`, každý s jednou krátkou větou (≤ 60 znaků).
- Pro krypto použij `yf_symbol` typu `BTC-USD`, `decimals: 0`.
- Pokud tým navrhl více setupů, kresli ten doporučený (nebo nejlépe hodnocený); ostatní zmiň v `caption`.

## 3. Vykresli

```bash
python3 .claude/skills/chart-report/render_chart.py --spec reports/AAPL_2026-10-24.json --out reports/AAPL_2026-10-24.png
# s daty od uživatele:
python3 .claude/skills/chart-report/render_chart.py --spec ... --csv cesta/k/data.csv --out ...
```

- Kód 2 + `DATA_UNAVAILABLE` → **nic nevymýšlej ani negeneruj** a řekni uživateli: „yfinance data nejdou stáhnout, pošli mi CSV se sloupci Date, Open, High, Low, Close (Volume)“. Spec JSON nech uložený, ať jde graf dokreslit, až CSV dorazí.
- Hotový PNG si prohlédni (Read) a zkontroluj, že popisky nepřekrývají svíčky ani sebe navzájem; případně uprav `path`, `horizon_bars` nebo `bars` a vykresli znovu.

## 4. Commit

`git add reports/<soubor>.png reports/<soubor>.json` a commit se zprávou `Add chart report <TICKER> <datum>`. Push podle pokynů uživatele.
