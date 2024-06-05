import pytest

import matplotlib.pyplot as plt

from mplchart.chart import Chart
from mplchart.samples import sample_prices
from mplchart.primitives import Candlesticks, Volume
from mplchart.indicators import SMA, EMA, RSI, ATR, ADX, MACD, PPO, SLOPE, BBANDS

FREQS = ["daily", "hourly", "minute"]

INDICATORS = [
    Volume(),
    SMA(50),
    EMA(50),
    RSI(),
    ATR(),
    ADX(),
    MACD(),
    PPO(),
    SLOPE(),
    BBANDS(),
]


@pytest.mark.parametrize("freq", FREQS)
def test_prices(freq):
    prices = sample_prices(freq=freq)
    assert len(prices) > 0


@pytest.mark.parametrize("freq", FREQS)
@pytest.mark.parametrize("indicator", INDICATORS, ids=str)
def test_chart(indicator, freq, max_bars=250):
    if indicator is None:
        indicator = SMA(50)

    prices = sample_prices(freq=freq)

    indicators = [Candlesticks(), indicator]

    chart = Chart(title="Test", max_bars=max_bars)
    chart.plot(prices, indicators)

    assert chart.count_axes() > 0

    plt.close()
