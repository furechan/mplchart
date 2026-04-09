"""Primitive tests — pandas and polars backends"""

import pytest
import matplotlib.pyplot as plt

from mplchart.chart import Chart
from mplchart.samples import sample_prices
from mplchart.primitives import (
    Candlesticks, OHLC, Price, Volume,
    LinePlot, AreaPlot, BarPlot,
    Peaks, ZigZag, Stripes, Markers,
)
from mplchart.indicators import SMA, RSI


FREQS = ["daily", "hourly", "minute"]
BACKENDS = ["pandas", "polars"]

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
    RSI() | Stripes(expr="close < 30"),
    RSI() | Markers(expr="close < 30"),
]


PANDAS_ONLY_PRIMITIVES = {
    str(SMA(20) | LinePlot()),
    str(SMA(20) | AreaPlot()),
    str(SMA(20) | BarPlot()),
    str(RSI() | Stripes(expr="close < 30")),
    str(RSI() | Markers(expr="close < 30")),
}


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("freq", FREQS)
@pytest.mark.parametrize("primitive", PRIMITIVES, ids=str)
def test_primitives(primitive, freq, backend):
    if backend == "polars":
        pytest.importorskip("polars")
        if str(primitive) in PANDAS_ONLY_PRIMITIVES:
            pytest.xfail("pandas indicators not compatible with polars input")
    prices = sample_prices(freq=freq, backend=backend)
    chart = Chart(prices, max_bars=100)
    chart.plot(primitive)
    assert chart.count_axes() > 0
    plt.close()
