import json

from scanner import lab_report as lr


class _State:
    def __init__(self, data):
        self.data = data


def _setup(tmp_path, monkeypatch, closes=()):
    monkeypatch.setattr(lr, "CACHE", tmp_path)
    log = tmp_path / "lab.jsonl"
    log.write_text("".join(json.dumps({"event": "close", "sid": "x", "r": r, "time": t}) + "\n" for t, r in closes))
    monkeypatch.setattr(lr, "LOG", log)
    st = _State({"lab": {"open": [
        {"sid": "a", "label": "Donchian průraz 100 · 1H long", "coin": "BTC", "tf": "1h", "dir": "long",
         "signal_close": 80000.0, "rf": 0.02},
        {"sid": "b", "label": "Keltner průraz 2.5 · 4H short", "coin": "ETH", "tf": "4h", "dir": "short",
         "signal_close": 2400.0, "rf": 0.03}]}, "open": []})
    prices = {"BTC/USDT": (80800.0, ""), "ETH/USDT": (2424.0, "")}
    return st, prices


def test_lines_show_r_and_percent_after_fees(tmp_path, monkeypatch):
    st, prices = _setup(tmp_path, monkeypatch)
    text = "\n".join(lr.lines(st, prices))
    assert "otevřené 2, uzavřené 0" in text
    assert "BTC LONG 1H" in text and "+0,45 R (+0,90 %)" in text        # +1 % − 0,1 % poplatky, riziko 2 %
    assert "ETH SHORT 4H" in text and "-0,37 R (-1,10 %)" in text       # short proti růstu o 1 %


def test_render_png_with_and_without_closed_trades(tmp_path, monkeypatch):
    st, prices = _setup(tmp_path, monkeypatch)
    assert lr.render(st, prices, tmp_path / "a.png").stat().st_size > 10_000
    st, prices = _setup(tmp_path, monkeypatch, [("2026-10-28T12:00:00+00:00", 1.2), ("2026-10-29T12:00:00+00:00", -0.5)])
    assert "Σ +0,70 R" in lr.lines(st, prices)[0]
    assert lr.render(st, prices, tmp_path / "b.png").stat().st_size > 10_000
