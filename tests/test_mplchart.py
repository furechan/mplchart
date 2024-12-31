import pytest

import matplotlib.pyplot as plt

from mplchart.chart import Chart
from mplchart.samples import sample_prices
from mplchart.primitives import Candlesticks, Volume
from mplchart.indicators import SMA, EMA, WMA, HMA, RSI, ATR, ATRP, ADX, MACD, PPO, TSF
from mplchart.indicators import SLOPE, BBANDS, STOCH

try:
    from talib import abstract
except ImportError:
    abstract = None


FREQS = ["daily", "hourly", "minute"]

INDICATORS = [
    Volume(),
    SMA(20),
    EMA(20),
    WMA(20),
    HMA(20),
    TSF(20),
    RSI(),
    ATR(),
    ATRP(),
    ADX(),
    MACD(),
    PPO(),
    SLOPE(),
    BBANDS(),
    STOCH()
]


@pytest.mark.parametrize("freq", FREQS)
def test_prices(freq):
    prices = sample_prices(freq=freq)
    assert len(prices) > 0


@pytest.mark.parametrize("freq", FREQS)
@pytest.mark.parametrize("indicator", INDICATORS, ids=str)
def test_indicators(indicator, freq, max_bars=250):
    if indicator is None:
        indicator = SMA(50)

    prices = sample_prices(freq=freq)

    indicators = [Candlesticks(), indicator]

    chart = Chart(title="Test", max_bars=max_bars)
    chart.plot(prices, indicators)

    assert chart.count_axes() > 0

    plt.close()


@pytest.mark.skipif(abstract is None, reason="requires talib")
@pytest.mark.parametrize("freq", FREQS)
def test_talib(freq, max_bars=250):
    prices = sample_prices(freq=freq)

    indicators = [
        Candlesticks(),
        abstract.Function("SMA", 50),
        abstract.Function("SMA", 200),
        abstract.Function("KAMA"),
        abstract.Function("BBANDS"),
        abstract.Function("RSI"),
        abstract.Function("MACD"),
    ]
   
    chart = Chart(title="Test", max_bars=max_bars)
    chart.plot(prices, indicators)

    assert chart.count_axes() > 0

    plt.close()
