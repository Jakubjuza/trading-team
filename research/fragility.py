#!/usr/bin/env python3
"""🧊 Křehkost trhu – jak BTC REAGUJE na zprávy: táhnou ho víc špatné, nebo dobré? Bez AI, jen z ceny.

Myšlenka (Jakub, 5. 11. 2026): stejná zpráva neznamená v každém trhu totéž. V býčím trhu se špatná zpráva „spolkne“
a dobrá pohyb zesílí. V křehkém trhu (po odrazu ode dna, strach z bull trapu) udělá špatná zpráva velký propad
a dobrá skoro nic. Nálada (bear/bull) tohle neříká – měří se tu REAKCE.

Jak se měří (1H svíčky BTC, nic z budoucnosti):
  šok      = hodina, kdy |výnos| ≥ 3σ (σ = směrodatná odchylka hodinových výnosů za předchozích 30 dní). Takové hodiny
             jsou skoro vždy zpráva (Fed, CPI, NFP, ETF toky, likvidace, geopolitika). Dolů = „špatná“, nahoru = „dobrá“.
  dotažení = výnos dalších 24 h ve směru šoku v jednotkách σ·√24: > 0 trh zprávu dotáhl, < 0 ji smazal.
  okno     = šoky za posledních 30 dní, jejichž 24 h už uplynulo.
  dopad    = (Σ|z| šoků dolů − Σ|z| šoků nahoru) / Σ|z| všech      (−1 … +1: kdo „dělá trh“)
  reakce   = (Ø dotažení dolů − Ø dotažení nahoru) / 2, ořez −1 … +1 (dotahuje trh špatné, a dobré maže?)
  K        = ½·dopad + ½·reakce;  K ≥ +0,25 🧊 křehký · K ≤ −0,25 🔥 nesený optimismem · jinak ⚖️ vyrovnaný
             (s < 4 šoky v okně se K nepočítá – málo dat).

Je to POPIS stavu, ne signál. Jestli pomáhá obchodům, měří research/experiments/fragility_test.py
(reports/fragility.md); pravidla skeneru se mění jen po testu.

    python3 research/fragility.py            # aktuální stav (stáhne 1H BTC)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SIGMA_H, Z, FT_H, WINDOW_D, MIN_SHOCKS, THR = 720, 3.0, 24, 30, 4, 0.25


def shocks(h1, sigma_h=SIGMA_H, z=Z, ft_h=FT_H):
    """Šokové hodiny: time, sign, z, ft (dotažení 24 h ve směru šoku v σ·√ft_h), known (kdy je ft známé)."""
    c = h1["Close"].astype(float)
    r = np.log(c).diff()
    sd = r.rolling(sigma_h, min_periods=sigma_h // 2).std().shift(1)          # σ jen z minulosti
    zz = r / sd
    fwd = np.log(c.shift(-ft_h) / c)                                           # dalších 24 h po zavření šokové hodiny
    m = zz.abs() >= z
    out = pd.DataFrame({"sign": np.sign(zz[m]), "z": zz[m], "ft": np.sign(zz[m]) * fwd[m] / (sd[m] * np.sqrt(ft_h))})
    out["known"] = out.index + pd.Timedelta(hours=ft_h)
    return out.dropna()


def score(sh):
    """K a jeho složky z tabulky šoků v okně. None, když je šoků málo."""
    if len(sh) < MIN_SHOCKS:
        return None
    dn, up = sh[sh["sign"] < 0], sh[sh["sign"] > 0]
    tot = sh["z"].abs().sum()
    impact = float((dn["z"].abs().sum() - up["z"].abs().sum()) / tot) if tot else 0.0
    ft_dn = float(dn["ft"].mean()) if len(dn) else 0.0
    ft_up = float(up["ft"].mean()) if len(up) else 0.0
    react = float(np.clip((ft_dn - ft_up) / 2, -1, 1))
    k = 0.5 * impact + 0.5 * react
    return {"k": round(k, 3), "impact": round(impact, 3), "react": round(react, 3), "n_dn": int(len(dn)),
            "n_up": int(len(up)), "ft_dn": round(ft_dn, 2), "ft_up": round(ft_up, 2)}


def state(k):
    if k is None or (isinstance(k, float) and np.isnan(k)):
        return "málo dat"
    return "křehký" if k >= THR else "optimistický" if k <= -THR else "vyrovnaný"


def series(h1, times, window_d=WINDOW_D, sh=None):
    """K v zadaných časech (jen šoky, jejichž dotažení je v daném čase už známé)."""
    sh = shocks(h1) if sh is None else sh
    vals = []
    for t in pd.DatetimeIndex(times):
        w = sh[(sh["known"] <= t).values & (sh.index >= t - pd.Timedelta(days=window_d))]
        s = score(w)
        vals.append(np.nan if s is None else s["k"])
    return pd.Series(vals, index=pd.DatetimeIndex(times))


def current(h1, now=None):
    sh = shocks(h1)
    now = h1.index[-1] if now is None else now
    w = sh[(sh["known"] <= now) & (sh.index >= now - pd.Timedelta(days=WINDOW_D))]
    s = score(w) or {"k": None, "n_dn": int((w["sign"] < 0).sum()), "n_up": int((w["sign"] > 0).sum())}
    prev = sh[(sh["known"] <= now - pd.Timedelta(days=7)) & (sh.index >= now - pd.Timedelta(days=WINDOW_D + 7))]
    p = score(prev)
    s["k_7d_ago"] = p["k"] if p else None
    s["state"] = state(s["k"])
    s["last"] = [{"time": t.strftime("%Y-%m-%d %H:00 UTC"), "z": round(float(r.z), 1),
                  "ft": None if r.known > now else round(float(r.ft), 2)}
                 for t, r in sh[sh.index >= now - pd.Timedelta(days=7)].tail(6).iterrows()]
    return s


def line(s):
    """Jeden řádek pro datový list / zprávu."""
    if s.get("k") is None:
        return f"🧊 Křehkost: málo šoků za 30 dní ({s.get('n_dn', 0)}↓ / {s.get('n_up', 0)}↑) – nehodnoceno"
    icon = {"křehký": "🧊", "optimistický": "🔥"}.get(s["state"], "⚖️")
    trend = "" if s.get("k_7d_ago") is None else f", před týdnem {s['k_7d_ago']:+.2f}"
    return (f"{icon} Křehkost trhu K {s['k']:+.2f} ({s['state']}{trend}) · šoky 30 dní {s['n_dn']}↓/{s['n_up']}↑ · "
            f"dotažení špatných {s['ft_dn']:+.2f}, dobrých {s['ft_up']:+.2f}")


def section_fragility(h1=None):
    """Sekce datového listu `fragility` (stav BTC, platí pro celý trh)."""
    if h1 is None:
        sys.path.insert(0, str(ROOT))
        from scanner import evaluate as ev
        h1 = ev.load_history("BTC/USDT", "crypto", "1h", 90, cache_dir=ROOT / "scanner" / "cache")
    if h1 is None or len(h1) < SIGMA_H:
        return {"error": "1H svíčky BTC nedostupné"}
    s = current(h1[["Open", "High", "Low", "Close"]].astype(float).iloc[:-1])
    s["line"] = line(s)
    s["how"] = ("K = jak trh reaguje na šoky (≥3σ hodiny ≈ zprávy) za 30 dní; + = špatné zprávy táhnou a dobré se smažou "
                "(křehký), − = naopak (optimistický). Popis, ne signál – test v reports/fragility.md.")
    return s


def main():
    s = section_fragility()
    if "error" in s:
        print(json.dumps(s, ensure_ascii=False))
        return
    print(line(s))
    print(json.dumps(s, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
