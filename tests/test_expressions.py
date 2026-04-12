"""Expression tests — polars backend"""

import pytest
import matplotlib.pyplot as plt

polars = pytest.importorskip("polars")

from mplchart.chart import Chart
from mplchart.samples import sample_prices
from mplchart.primitives import Candlesticks
from mplchart.expressions import (
    SMA, EMA, RMA, WMA, HMA, DEMA, TEMA,
    RSI, MACD, STOCH, ROC, MOM,
    TRANGE, ATR, BBANDS, DONCHIAN, KELTNER,
    MIDPRICE, TYPPRICE, WCLPRICE,
)


FREQS = ["daily", "hourly", "minute"]

EXPRESSIONS = [
    SMA(20),
    EMA(20),
    RMA(14),
    WMA(20),
    HMA(20),
    DEMA(20),
    TEMA(20),
    RSI(14),
    MACD(12, 26, 9),
    STOCH(),
    ROC(14),
    MOM(14),
    TRANGE(),
    ATR(14),
    BBANDS(20),
    DONCHIAN(20),
    KELTNER(20),
    MIDPRICE(),
    TYPPRICE(),
    WCLPRICE(),
]


@pytest.mark.parametrize("freq", FREQS)
def test_prices(freq):
    prices = sample_prices(freq=freq, backend="polars")
    assert len(prices) > 0
    assert hasattr(prices, "schema")


@pytest.mark.parametrize("freq", FREQS)
def test_chart_init(freq):
    prices = sample_prices(freq=freq, backend="polars")
    chart = Chart(prices, max_bars=100)
    assert chart.prices is not None
    assert chart.backend == "polars"
    plt.close()


@pytest.mark.parametrize("freq", FREQS)
@pytest.mark.parametrize("expr", EXPRESSIONS, ids=str)
def test_expressions(expr, freq):
    prices = sample_prices(freq=freq, backend="polars")
    chart = Chart(prices, max_bars=100)
    chart.plot([Candlesticks(), expr])
    assert chart.count_axes() > 0
    plt.close()
