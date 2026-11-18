import numpy as np

from research.experiments import ifvg_study as S


def _bars():
    # svíčky 0–2: medvědí FVG (high[2]=95 < low[0]=100), svíčka 4 zavře nad 100 → long IFVG; 5 retest zóny
    h = np.array([105, 99, 95, 97, 103, 101, 104], float)
    l = np.array([100, 94, 90, 92, 96, 98, 100], float)
    c = np.array([101, 95, 92, 96, 102, 100.5, 103], float)
    atr = np.full(len(c), 2.0)
    return h, l, c, atr


def test_long_ifvg_inversion_and_retest():
    h, l, c, atr = _bars()
    inv = S.ifvg_marks(h, l, c, atr, 1.0, 0.0, 10, False, 5)
    assert list(np.flatnonzero(inv)) == [4]                    # první close nad horní hranou zóny (100)
    ret = S.ifvg_marks(h, l, c, atr, 1.0, 0.0, 10, True, 5)
    assert list(np.flatnonzero(ret)) == [5]                    # low 98 ≤ 100 a close 100,5 nad spodní hranou 95


def test_gap_size_filter_and_window():
    h, l, c, atr = _bars()
    assert not S.ifvg_marks(h, l, c, atr, 1.0, 3.0, 10, False, 5).any()   # zóna 5 < 3 × ATR 2
    assert not S.ifvg_marks(h, l, c, atr, 1.0, 0.0, 1, False, 5).any()    # překlopení až 2 svíčky po vzniku


def test_short_is_mirror():
    h, l, c, atr = _bars()
    inv = S.ifvg_marks(-l, -h, -c, atr, -1.0, 0.0, 10, False, 5)
    assert list(np.flatnonzero(inv)) == [4]
