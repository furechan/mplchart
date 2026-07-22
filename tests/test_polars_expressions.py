"""Expression tests — polars backend"""

import pytest
import matplotlib.pyplot as plt

polars = pytest.importorskip("polars")
pytestmark = pytest.mark.polars

import polars as pl  # noqa: E402

from mplchart.chart import Chart  # noqa: E402
from mplchart.samples import sample_prices  # noqa: E402
from mplchart.primitives import Candlesticks  # noqa: E402
from mplchart.utils import get_label  # noqa: E402
from mplchart.dataview import get_view  # noqa: E402
from mplchart.expressions import (  # noqa: E402
    SMA, EMA, RMA, WMA, HMA, DEMA, TEMA,
    RSI, MACD, STOCH, ROC, MOM,
    TRANGE, ATR, BBANDS, DONCHIAN, KELTNER,
    AVGPRICE, MEDPRICE, TYPPRICE, WCLPRICE,
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
    MEDPRICE(),
    AVGPRICE(),
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
    assert chart.view is not None
    assert chart.view.prices is not None
    assert chart.backend == "polars"
    plt.close()


@pytest.mark.parametrize("freq", FREQS)
@pytest.mark.parametrize("expr", EXPRESSIONS, ids=str)
def test_expressions(expr, freq):
    prices = sample_prices(freq=freq, backend="polars")
    chart = Chart(prices, max_bars=100)
    chart.plot([Candlesticks(), expr])
    assert chart.canvas.count_axes() > 0
    plt.close()


def test_eval_struct_expr():
    prices = sample_prices(backend="polars")
    expr = MACD()
    assert isinstance(expr, pl.Expr)  # multi-output expressions are now struct Exprs
    result = get_view(prices).eval(expr)
    assert isinstance(result, pl.DataFrame)
    assert list(result.columns) == ["macd", "macdsignal", "macdhist"]
    assert len(result) == len(prices)


def test_struct_expr_alias_as_label():
    expr = MACD(12, 26, 9)
    assert get_label(expr) == "macd-12-26-9"

    # custom alias overrides the default
    custom = expr.alias("my-macd")
    assert get_label(custom) == "my-macd"

    prices = sample_prices(backend="polars")
    result = get_view(prices).eval(custom)
    assert list(result.columns) == ["macd", "macdsignal", "macdhist"]
