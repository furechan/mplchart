"""Primitive tests — pandas backend"""

import pytest
import matplotlib.pyplot as plt

pytest.importorskip("pandas")
pytestmark = pytest.mark.pandas

try:
    from pandas.api.typing import Expression  # noqa: F401
    pd_has_expressions = True
except ImportError:
    pd_has_expressions = False

from mplchart.chart import Chart  # noqa: E402
from mplchart.samples import sample_prices  # noqa: E402
from mplchart.primitives import (  # noqa: E402
    Candlesticks, HeikinAshi, OHLC, Volume,
    Line, Area, Bars,
    Swings, ZigZag, Stripes, Markers,
    HLine, VLine, TrendLines,
)
from mplchart.indicators import SMA, RSI  # noqa: E402


FREQS = ["daily", "hourly", "minute"]

PRIMITIVES = [
    Candlesticks(),
    HeikinAshi(),
    OHLC(),
    Line("close"),
    Volume(),
    SMA(20) @ Line(),
    SMA(20) @ Area(),
    SMA(20) @ Bars(),
    Swings(),
    ZigZag(),
    ZigZag(color="purple"),
    TrendLines(),
    HLine(25),
    HLine(25, color="red", linestyle="dashed"),
]

if pd_has_expressions:
    PRIMITIVES += [
        Stripes(RSI().as_expr() < 30),
        Markers(RSI().as_expr() < 30),
    ]


@pytest.mark.parametrize("freq", FREQS)
@pytest.mark.parametrize("primitive", PRIMITIVES, ids=str)
def test_primitives(primitive, freq):
    prices = sample_prices(freq=freq, backend="pandas")
    chart = Chart(prices, max_bars=100)
    chart.plot(primitive)
    assert chart.canvas.count_axes() > 0
    plt.close()


@pytest.mark.parametrize("freq", FREQS)
def test_vline(freq):
    prices = sample_prices(freq=freq, backend="pandas")
    date = prices.index[len(prices) // 2]
    chart = Chart(prices, max_bars=100)
    chart.plot(Candlesticks(), VLine(date))
    assert chart.canvas.count_axes() > 0
    plt.close()


@pytest.mark.parametrize("freq", FREQS)
def test_vline_method(freq):
    prices = sample_prices(freq=freq, backend="pandas")
    date = prices.index[len(prices) // 2]
    chart = Chart(prices, max_bars=100)
    chart.plot(Candlesticks()).vline(date)
    assert chart.canvas.count_axes() > 0
    plt.close()


@pytest.mark.parametrize("freq", FREQS)
def test_hline_method(freq):
    prices = sample_prices(freq=freq, backend="pandas")
    chart = Chart(prices, max_bars=100)
    chart.plot(Candlesticks()).hline(25, color="red")
    assert chart.canvas.count_axes() > 0
    plt.close()
