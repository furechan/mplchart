"""Primitive tests — polars backend"""

import pytest
import matplotlib.pyplot as plt

pytest.importorskip("polars")
pytestmark = pytest.mark.polars

from mplchart.chart import Chart  # noqa: E402
from mplchart.samples import sample_prices  # noqa: E402
from mplchart.primitives import (  # noqa: E402
    Candlesticks, OHLC, Volume,
    AutoPlot, LinePlot, AreaPlot, BarPlot,
    Swings, ZigZag, Stripes, Markers,
    HLine, VLine, TrendLines,
)
from mplchart.expressions import SMA, RSI, MACD  # noqa: E402


FREQS = ["daily", "hourly", "minute"]

PRIMITIVES = [
    Candlesticks(),
    OHLC(),
    LinePlot("close"),
    Volume(),
    SMA(20) @ AutoPlot(),
    SMA(20) @ AutoPlot(label="short_ma"),
    MACD() @ AutoPlot(label="macd"),
    SMA(20) @ LinePlot(),
    SMA(20) @ AreaPlot(),
    SMA(20) @ BarPlot(),
    Swings(),
    ZigZag(),
    TrendLines(),
    (RSI() < 0.30) @ Stripes(),
    (RSI() < 0.30) @ Markers(),
    HLine(25),
    HLine(25, color="red", linestyle="dashed"),
]


@pytest.mark.parametrize("freq", FREQS)
@pytest.mark.parametrize("primitive", PRIMITIVES, ids=str)
def test_primitives(primitive, freq):
    prices = sample_prices(freq=freq, backend="polars")
    chart = Chart(prices, max_bars=100)
    chart.plot(primitive)
    assert chart.canvas.count_axes() > 0
    plt.close()


@pytest.mark.parametrize("freq", FREQS)
def test_vline(freq):
    prices = sample_prices(freq=freq, backend="polars")
    date = prices.row(len(prices) // 2)[0]
    chart = Chart(prices, max_bars=100)
    chart.plot(Candlesticks(), VLine(date))
    assert chart.canvas.count_axes() > 0
    plt.close()


@pytest.mark.parametrize("freq", FREQS)
def test_vline_method(freq):
    prices = sample_prices(freq=freq, backend="polars")
    date = prices.row(len(prices) // 2)[0]
    chart = Chart(prices, max_bars=100)
    chart.plot(Candlesticks()).vline(date)
    assert chart.canvas.count_axes() > 0
    plt.close()


@pytest.mark.parametrize("freq", FREQS)
def test_hline_method(freq):
    prices = sample_prices(freq=freq, backend="polars")
    chart = Chart(prices, max_bars=100)
    chart.plot(Candlesticks()).hline(25, color="red")
    assert chart.canvas.count_axes() > 0
    plt.close()
