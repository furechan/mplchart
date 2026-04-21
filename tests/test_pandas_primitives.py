"""Primitive tests — pandas backend"""

import pytest
import matplotlib.pyplot as plt

pytest.importorskip("pandas")
pytestmark = pytest.mark.pandas

from mplchart.chart import Chart  # noqa: E402
from mplchart.samples import sample_prices  # noqa: E402
from mplchart.primitives import (  # noqa: E402
    Candlesticks, OHLC, Price, Volume,
    LinePlot, AreaPlot, BarPlot,
    Peaks, ZigZag, Stripes, Markers,
)
from mplchart.indicators import SMA, RSI  # noqa: E402


FREQS = ["daily", "hourly", "minute"]

PRIMITIVES = [
    Candlesticks(),
    OHLC(),
    Price(),
    Volume(),
    SMA(20) | LinePlot(),
    SMA(20) | AreaPlot(),
    SMA(20) | BarPlot(),
    Peaks(),
    ZigZag(),
    RSI() | Stripes(expr=lambda s: s < 30),
    RSI() | Markers(expr=lambda s: s < 30),
]


@pytest.mark.parametrize("freq", FREQS)
@pytest.mark.parametrize("primitive", PRIMITIVES, ids=str)
def test_primitives(primitive, freq):
    prices = sample_prices(freq=freq, backend="pandas")
    chart = Chart(prices, max_bars=100)
    chart.plot(primitive)
    assert chart.count_axes() > 0
    plt.close()
