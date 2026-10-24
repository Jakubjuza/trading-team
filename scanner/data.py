"""Svíčky s lokální cache: stahuje jen nové svíčky (yfinance pro akcie, ccxt pro krypto)."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

COLS = ["Open", "High", "Low", "Close", "Volume"]
TF_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}
# yfinance nemá 4h → stahuje se 1h a převzorkuje
YF_BASE = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "60m", "4h": "60m", "1d": "1d"}
YF_MAX_DAYS = {"1m": 7, "5m": 59, "15m": 59, "30m": 59, "60m": 729, "1d": 3650}


def _empty():
    return pd.DataFrame(columns=COLS, index=pd.DatetimeIndex([], tz="UTC", name="Time"))


class CandleCache:
    def __init__(self, cache_dir, history_bars=300, exchange="kraken", fetchers=None):
        self.dir = Path(cache_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.history_bars = history_bars
        self.exchange_id = exchange
        self._exchange = None
        # fetchers lze podstrčit v testech: {"crypto": fn, "stock": fn}
        self.fetchers = fetchers or {"crypto": self._fetch_ccxt, "stock": self._fetch_yf}

    # --- cache na disku -------------------------------------------------
    def _path(self, source, symbol, tf):
        safe = symbol.replace("/", "-").replace(":", "-")
        return self.dir / f"{source}_{safe}_{tf}.csv"

    def load(self, source, symbol, tf):
        p = self._path(source, symbol, tf)
        if not p.exists():
            return _empty()
        df = pd.read_csv(p, index_col=0)
        df.index = pd.to_datetime(df.index, utc=True)
        df.index.name = "Time"
        return df[COLS].astype(float)

    def save(self, source, symbol, tf, df):
        df.to_csv(self._path(source, symbol, tf))

    # --- aktualizace ----------------------------------------------------
    def update(self, source, symbol, tf, now=None):
        """Doplní nové svíčky do cache a vrátí jen UZAVŘENÉ svíčky rámce tf."""
        base_tf = "1h" if (source == "stock" and tf == "4h") else tf
        cached = self.load(source, symbol, base_tf)
        step = timedelta(minutes=TF_MINUTES[base_tf])
        if cached.empty:
            # akcie se obchodují jen část dne → vzít delší okno, ať je svíček dost
            span = self.history_bars * (1 if source == "crypto" or base_tf == "1d" else 4)
            since = (now or datetime.now(timezone.utc)) - step * span
        else:
            # poslední uložená svíčka mohla být rozpracovaná → stáhnout znovu od ní
            since = cached.index[-1].to_pydatetime()
        new = self.fetchers[source](symbol, base_tf, since)
        if new is not None and not new.empty:
            merged = pd.concat([cached, new[COLS].astype(float)])
            merged = merged[~merged.index.duplicated(keep="last")].sort_index()
        else:
            merged = cached
        merged = merged.iloc[-self.history_bars * (4 if base_tf != tf else 1):]
        self.save(source, symbol, base_tf, merged)
        out = resample(merged, tf) if base_tf != tf else merged
        return closed_only(out, tf, now)

    # --- zdroje ---------------------------------------------------------
    def _fetch_ccxt(self, symbol, tf, since):
        import ccxt
        if self._exchange is None:
            self._exchange = getattr(ccxt, self.exchange_id)({"enableRateLimit": True})
        rows = self._exchange.fetch_ohlcv(symbol, timeframe=tf, since=int(since.timestamp() * 1000), limit=1000)
        if not rows:
            return _empty()
        df = pd.DataFrame(rows, columns=["ts"] + COLS)
        df.index = pd.to_datetime(df.pop("ts"), unit="ms", utc=True)
        df.index.name = "Time"
        return df

    def _fetch_yf(self, symbol, tf, since):
        import yfinance as yf
        interval = YF_BASE[tf]
        earliest = datetime.now(timezone.utc) - timedelta(days=YF_MAX_DAYS[interval])
        start = max(since - timedelta(minutes=TF_MINUTES[tf]), earliest)
        df = yf.download(symbol, start=start, interval=interval, progress=False, auto_adjust=False)
        if df is None or df.empty:
            return _empty()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index, utc=True)
        df.index.name = "Time"
        return df[COLS]


def resample(df, tf):
    rule = {"4h": "4h", "1d": "1D"}.get(tf, tf.replace("m", "min"))
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    return df.resample(rule, origin="epoch").agg(agg).dropna()


def closed_only(df, tf, now=None):
    """Zahodí svíčky, které ještě nejsou uzavřené."""
    now = now or datetime.now(timezone.utc)
    end = df.index + pd.Timedelta(minutes=TF_MINUTES[tf])
    return df[end <= now]
