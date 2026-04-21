"""Chart tests for pandas native expressions (pd.col)"""

import pytest
import matplotlib.pyplot as plt

pd = pytest.importorskip("pandas", minversion="3.0")
pytestmark = pytest.mark.pandas

from mplchart.chart import Chart  # noqa: E402
from mplchart.samples import sample_prices  # noqa: E402
from mplchart.primitives import Candlesticks, Volume  # noqa: E402
from mplchart.utils import is_pandas_expr  # noqa: E402


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
    assert chart.count_axes() > 0
    plt.close()


def test_plot_expression_pane():
    body = (pd.col("close") - pd.col("open")).abs()
    chart = Chart(prices(), max_bars=100)
    chart.plot(Candlesticks(), Volume()).pane("below").plot(body)
    assert chart.count_axes() > 0
    plt.close()
