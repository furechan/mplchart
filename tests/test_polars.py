"""Polars tests — baseline + expression factories"""

import pytest

import matplotlib.pyplot as plt

polars = pytest.importorskip("polars")

from mplchart.chart import Chart
from mplchart.samples import sample_prices
from mplchart.primitives import Candlesticks
from mplchart.indicators import SMA, EMA, RSI, MACD, BBANDS
from mplchart.expressions import SMA as xSMA, EMA as xEMA, RSI as xRSI, MACD as xMACD, BBANDS as xBBANDS


FREQS = ["daily", "hourly", "minute"]


@pytest.mark.parametrize("freq", FREQS)
def test_polars_prices(freq):
    prices = sample_prices(freq=freq, backend="polars")
    assert len(prices) > 0
    assert hasattr(prices, "schema")   # polars DataFrame


@pytest.mark.parametrize("freq", FREQS)
def test_polars_chart_init(freq):
    prices = sample_prices(freq=freq, backend="polars")
    chart = Chart(prices, max_bars=100)
    assert chart.prices is not None
    assert chart.backend == "polars"
    plt.close()


@pytest.mark.parametrize("freq", FREQS)
def test_polars_candlesticks(freq):
    prices = sample_prices(freq=freq, backend="polars")
    chart = Chart(prices, max_bars=100)
    chart.plot(Candlesticks())
    plt.close()


@pytest.mark.xfail(reason="pandas indicators not yet compatible with polars input")
@pytest.mark.parametrize("freq", FREQS)
@pytest.mark.parametrize("indicator", [SMA(20), EMA(20), RSI(), MACD(), BBANDS()], ids=str)
def test_polars_pandas_indicators(indicator, freq):
    prices = sample_prices(freq=freq, backend="polars")
    chart = Chart(prices, max_bars=100)
    chart.plot([Candlesticks(), indicator])
    plt.close()


@pytest.mark.parametrize("freq", FREQS)
@pytest.mark.parametrize("expr,label", [
    (xSMA(20), "SMA"),
    (xEMA(20), "EMA"),
    (xRSI(14), "RSI"),
    (xMACD(12, 26, 9), "MACD"),
    (xBBANDS(20), "BBANDS"),
], ids=lambda x: x if isinstance(x, str) else "")
def test_polars_expressions(expr, label, freq):
    prices = sample_prices(freq=freq, backend="polars")
    chart = Chart(prices, max_bars=100)
    chart.plot([Candlesticks(), expr])
    plt.close()
