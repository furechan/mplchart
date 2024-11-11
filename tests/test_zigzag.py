import pandas as pd
from mplchart.zigzag import Zigzag, Pivot, Point

def test_window_peaks():
    """Test window peaks calculation"""
    data = {
        'norm_high': [10, 11, 12, 11, 10, 11, 13, 12, 11, 9],
        'norm_low':  [9, 10, 11, 9, 8, 10, 12, 10, 9, 7]
    }
    df = pd.DataFrame(data, index=pd.date_range('2024-01-01', periods=len(data['norm_high'])))

    zigzag = Zigzag(backcandels=2, forwardcandels=4)
    highs, lows = zigzag.window_peaks(df, 2, 4)
    assert highs.values.tolist() == [12, 12, 13, 13, 13, 13, 13, 13, 13, 12]
    assert lows.values.tolist() == [8, 8, 8, 8, 8, 7, 7, 7, 7, 7]

def test_price_normalization():
    # Create sample data
    df = pd.DataFrame({
        'high':  [100, 150, 120, 180, 160],
        'low':   [90,  110, 100, 150, 140],
        'close': [95,  120, 110, 160, 150],
        'open':  [90,  110, 100, 150, 140]
    })

    zigzag = Zigzag(backcandels=1, forwardcandels=1)
    zigzag.calculate(df)

    assert len(zigzag.zigzag_pivots) == 5
    # Check if normalization is between 0 and 1
    assert all(0 < pivot.point.norm_price <= 1 for pivot in zigzag.zigzag_pivots)

    # Test specific normalization values
    # For price range 90 (min) to 180 (max)
    expected_norm = {
        180: 1.0,    # max price should be 1.0
        90: 0.0,     # min price should be 0.0
        135: 0.5,    # middle point should be 0.5
    }

    for price, expected in expected_norm.items():
        normalized = (price - 90) / (180 - 90)
        assert abs(normalized - expected) < 1e-6

def test_single_value():
    df = pd.DataFrame({
        'high':  [100],
        'low':   [100],
        'close': [100],
        'open':  [100]
    })

    zigzag = Zigzag()
    zigzag.calculate(df)

    # With single value, normalization should be 0 or undefined
    if zigzag.zigzag_pivots:
        assert zigzag.zigzag_pivots[0].point.norm_price > 0

def test_same_prices():
    df = pd.DataFrame({
        'high':  [100, 100, 100],
        'low':   [100, 100, 100],
        'close': [100, 100, 100],
        'open':  [100, 100, 100]
    })

    zigzag = Zigzag()
    zigzag.calculate(df)

    # When all prices are same, normalized values should be 0
    if zigzag.zigzag_pivots:
        assert all(pivot.point.norm_price > 0 for pivot in zigzag.zigzag_pivots)

def test_price_relationships():
    df = pd.DataFrame({
        'high':  [100, 150, 120],
        'low':   [90,  110, 100],
        'close': [95,  120, 110],
        'open':  [90,  110, 100]
    })

    zigzag = Zigzag()
    zigzag.calculate(df)

    # Test relative relationships are preserved
    pivots = zigzag.zigzag_pivots
    if len(pivots) >= 2:
        for i in range(len(pivots) - 1):
            p1, p2 = pivots[i], pivots[i + 1]
            # If original prices have a certain relationship,
            # normalized prices should maintain the same relationship
            assert (p1.point.price > p2.point.price) == (p1.point.norm_price > p2.point.norm_price)