"""Chart tests for pandas native expressions (pd.col)"""

import pytest
import matplotlib.pyplot as plt

pd = pytest.importorskip("pandas", minversion="3.0")
pytestmark = pytest.mark.pandas

from mplchart.chart import Chart  # noqa: E402
from mplchart.samples import sample_prices  # noqa: E402
from mplchart.primitives import Candlesticks, Volume  # noqa: E402
from mplchart.indicators import RSI, SMA, MACD, BBANDS  # noqa: E402
from mplchart.utils import is_pandas_expr  # noqa: E402
from mplchart.dataview import get_view  # noqa: E402


def prices():
    return sample_prices(backend="pandas")


EXPRESSIONS = [
    pd.col("close"),
    pd.col("close").rolling(20).mean(),
    pd.col("close").rolling(50).mean(),
    (pd.col("close") - pd.col("open")).abs(),
]


def test_is_pandas_expr():
    assert is_pandas_expr(pd.col("close"))
    assert not is_pandas_expr(lambda df: df["close"])
    assert not is_pandas_expr("close")


@pytest.mark.parametrize("expr", EXPRESSIONS, ids=repr)
def test_plot_expression(expr):
    chart = Chart(prices(), max_bars=100)
    chart.plot(Candlesticks(), expr)
    assert chart.canvas.count_axes() > 0
    plt.close()


def test_plot_expression_pane():
    body = (pd.col("close") - pd.col("open")).abs()
    chart = Chart(prices(), max_bars=100)
    chart.plot(Candlesticks(), Volume()).pane("below").plot(body)
    assert chart.canvas.count_axes() > 0
    plt.close()


def test_indicator_as_expr_single_output():
    expr = RSI(14).as_expr()
    assert is_pandas_expr(expr)
    assert repr(expr) == "RSI(14)"

    composed = RSI(14).as_expr() < 30
    assert is_pandas_expr(composed)

    result = get_view(prices()).eval(composed)
    assert result.dtype == bool


def test_indicator_as_expr_default_params():
    expr = SMA().as_expr()
    assert is_pandas_expr(expr)


@pytest.mark.parametrize("indicator", [MACD(), BBANDS()], ids=repr)
def test_indicator_as_expr_rejects_multi_output(indicator):
    with pytest.raises(TypeError, match="requires an item"):
        indicator.as_expr()


def test_indicator_as_expr_with_item():
    expr = MACD().as_expr("macdhist")
    assert is_pandas_expr(expr)
    assert repr(expr).endswith(".macdhist")

    composed = MACD().as_expr("macdhist") > 0
    result = get_view(prices()).eval(composed)
    assert result.dtype == bool


def test_indicator_as_expr_unknown_item():
    with pytest.raises(ValueError, match="not an output"):
        MACD().as_expr("nope")


def test_indicator_as_expr_item_on_single_output():
    with pytest.raises(TypeError, match="single-output"):
        RSI().as_expr("anything")
