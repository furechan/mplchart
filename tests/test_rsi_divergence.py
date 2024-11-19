import pytest
import pandas as pd
import numpy as np
from mplchart.rsi_div_patterns import calc_rsi

@pytest.fixture
def sample_prices():
    """Create sample price DataFrame with OHLC data"""
    return pd.DataFrame({
        'open':  [99, 101, 103, 102, 105, 104, 106, 107, 105, 104,  # First 10
                 106, 107, 108, 109, 108, 107, 106, 105, 104, 103], # Next 10
        'high':  [101, 103, 105, 104, 107, 106, 108, 109, 107, 106,
                 108, 109, 110, 111, 110, 109, 108, 107, 106, 105],
        'low':   [98, 100, 102, 101, 104, 103, 105, 106, 104, 103,
                 105, 106, 107, 108, 107, 106, 105, 104, 103, 102],
        'close': [100, 102, 104, 103, 106, 105, 107, 108, 106, 105,
                 107, 108, 109, 110, 109, 108, 107, 106, 105, 104]
    }, index=pd.date_range(start='2024-01-01', periods=20, freq='D'))

def test_rsi_basic_calculation(sample_prices):
    """Test basic RSI calculation with default period"""
    rsi = calc_rsi(sample_prices)

    # RSI should be between 0 and 100
    assert all(0 <= x <= 100 for x in rsi.dropna())

    # First period-1 values should be NaN
    assert rsi[:14].isna().all()

    # Should have valid values after period
    assert rsi[14:].notna().all()

def test_rsi_uptrend():
    """Test RSI calculation in strong uptrend"""
    # Create consistently rising prices
    dates = pd.date_range(start='2024-01-01', periods=20, freq='D')
    uptrend = pd.DataFrame({
        'open':  [99 + i for i in range(20)],
        'high':  [101 + i for i in range(20)],
        'low':   [98 + i for i in range(20)],
        'close': [100 + i for i in range(20)]
    }, index=dates)

    rsi = calc_rsi(uptrend, period=14)

    # RSI should be high (>70) in strong uptrend
    valid_rsi = rsi.dropna()
    assert all(x > 70 for x in valid_rsi[-3:])

def test_rsi_downtrend():
    """Test RSI calculation in strong downtrend"""
    # Create consistently falling prices
    dates = pd.date_range(start='2024-01-01', periods=20, freq='D')
    downtrend = pd.DataFrame({
        'open':  [99 - i for i in range(20)],
        'high':  [101 - i for i in range(20)],
        'low':   [98 - i for i in range(20)],
        'close': [100 - i for i in range(20)]
    }, index=dates)

    rsi = calc_rsi(downtrend, period=14)

    # RSI should be low (<30) in strong downtrend
    valid_rsi = rsi.dropna()
    assert all(x < 30 for x in valid_rsi[-3:])

def test_rsi_flat():
    """Test RSI calculation with flat prices"""
    # Create flat price series
    dates = pd.date_range(start='2024-01-01', periods=20, freq='D')
    flat = pd.DataFrame({
        'open':  [99] * 20,
        'high':  [101] * 20,
        'low':   [98] * 20,
        'close': [100] * 20
    }, index=dates)

    rsi = calc_rsi(flat, period=14)

    # RSI should be exactly 50 for flat prices (after initial period)
    valid_rsi = rsi.dropna()
    assert all(abs(x - 50) < 1e-10 for x in valid_rsi)

def test_rsi_alternating():
    """Test RSI calculation with alternating up/down prices"""
    dates = pd.date_range(start='2024-01-01', periods=20, freq='D')
    alternating = pd.DataFrame({
        'open':  [99 + (i % 2) * 2 for i in range(20)],
        'high':  [101 + (i % 2) * 2 for i in range(20)],
        'low':   [98 + (i % 2) * 2 for i in range(20)],
        'close': [100 + (i % 2) * 2 for i in range(20)]
    }, index=dates)

    rsi = calc_rsi(alternating, period=14)

    # RSI should be near 50 for alternating prices
    valid_rsi = rsi.dropna()
    assert all(40 < x < 60 for x in valid_rsi[-3:])

def test_rsi_empty():
    """Test RSI calculation with empty DataFrame"""
    empty = pd.DataFrame(columns=['open', 'high', 'low', 'close'])
    rsi = calc_rsi(empty)
    assert len(rsi) == 0

def test_rsi_single_value():
    """Test RSI calculation with single value"""
    single = pd.DataFrame({
        'open':  [99],
        'high':  [101],
        'low':   [98],
        'close': [100]
    }, index=pd.date_range(start='2024-01-01', periods=1))

    rsi = calc_rsi(single)
    assert len(rsi) == 1
    assert np.isnan(rsi.iloc[0])

def test_rsi_with_gaps():
    """Test RSI calculation with missing values"""
    dates = pd.date_range(start='2024-01-01', periods=10, freq='D')
    prices = pd.DataFrame({
        'open':  [99, np.nan, 101, 102, np.nan, 104, 105, 106, 107, 108],
        'high':  [101, np.nan, 103, 104, np.nan, 106, 107, 108, 109, 110],
        'low':   [98, np.nan, 100, 101, np.nan, 103, 104, 105, 106, 107],
        'close': [100, np.nan, 102, 103, np.nan, 105, 106, 107, 108, 109]
    }, index=dates)

    rsi = calc_rsi(prices, period=5)

    # Should handle NaN values
    assert not rsi.isna().all()
    assert rsi.isna().any()
