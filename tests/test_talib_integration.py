import pytest
import matplotlib.pyplot as plt

from mplchart.chart import Chart
from mplchart.samples import sample_prices
from mplchart.primitives import Candlesticks

abstract = pytest.importorskip("talib.abstract")


FREQS = ["daily", "hourly", "minute"]


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
