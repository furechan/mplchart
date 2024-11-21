import pandas as pd
from mplchart.zigzag import Zigzag, window_peaks

def test_window_peaks():
    """Test window peaks calculation"""
    data = {
        'high': [10, 11, 12, 11, 10, 11, 13, 12, 11, 9],
        'low':  [9, 10, 11, 9, 8, 10, 12, 10, 9, 7]
    }
    df = pd.DataFrame(data, index=pd.date_range('2024-01-01', periods=len(data['high'])))

    highs, lows = window_peaks(df, 2, 4)
    assert highs.values.tolist() == [12, 12, 13, 13, 13, 13, 13, 13, 13, 12]
    assert lows.values.tolist() == [8, 8, 8, 8, 8, 7, 7, 7, 7, 7]

def test_single_value():
    df = pd.DataFrame({
        'high':  [100],
        'low':   [100],
        'close': [100],
        'open':  [100]
    })

    zigzag = Zigzag()
    zigzag.calculate(df)

    if zigzag.zigzag_pivots:
        assert zigzag.zigzag_pivots[0].point.price > 0

def test_same_prices():
    df = pd.DataFrame({
        'high':  [100, 100, 100],
        'low':   [100, 100, 100],
        'close': [100, 100, 100],
        'open':  [100, 100, 100]
    })

    zigzag = Zigzag()
    zigzag.calculate(df)

    if zigzag.zigzag_pivots:
        assert all(pivot.point.price > 0 for pivot in zigzag.zigzag_pivots)
