"""Talib function tests — polars backend"""

import pytest
import matplotlib.pyplot as plt

pytest.importorskip("polars")
abstract = pytest.importorskip("talib.abstract")
pytestmark = [pytest.mark.polars, pytest.mark.talib]

from mplchart.chart import Chart  # noqa: E402
from mplchart.samples import sample_prices  # noqa: E402
from mplchart.primitives import Candlesticks  # noqa: E402


FREQS = ["daily", "hourly", "minute"]


@pytest.mark.parametrize("freq", FREQS)
def test_talib(freq, max_bars=250):
    prices = sample_prices(freq=freq, backend="polars")

    indicators = [
        Candlesticks(),
        abstract.Function("SMA", 50),
        abstract.Function("SMA", 200),
        abstract.Function("KAMA"),
        abstract.Function("BBANDS"),
        abstract.Function("RSI"),
        abstract.Function("MACD"),
    ]

    chart = Chart(prices, title="Test", max_bars=max_bars)
    chart.plot(indicators)

    assert chart.count_axes() > 0

    plt.close()
