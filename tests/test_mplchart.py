import pytest

import matplotlib.pyplot as plt

from mplchart.chart import Chart
from mplchart.samples import sample_prices
from mplchart.primitives import Candlesticks, Volume
from mplchart.indicators import SMA, EMA, RSI, ATR, ADX, MACD, PPO, SLOPE, BBANDS
from mplchart.datamodels import ChartPoint

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

    halfway = len(prices) // 2

    chart_point = [
        ChartPoint(
            datetime=str(prices.index[halfway]),
            price=prices.iloc[halfway]['close'],
            label="Test Point",
            arrow=True
        )
    ]
    chart = Chart(title="Test", max_bars=max_bars)
    chart.plot(prices, indicators)

    chart.plot_points(chart_point)

    assert chart.count_axes() > 0

    plt.close()
