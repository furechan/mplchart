"""mintalib expressions — polars backend"""

import pytest
import matplotlib.pyplot as plt

pytest.importorskip("polars")
mintalib = pytest.importorskip("mintalib")
pytestmark = [pytest.mark.polars, pytest.mark.mintalib]

from mplchart.chart import Chart  # noqa: E402
from mplchart.samples import sample_prices  # noqa: E402
from mplchart.primitives import Candlesticks  # noqa: E402
from mintalib.expressions import (  # noqa: E402
    SMA, EMA, WMA, HMA, DEMA, TEMA,
    RSI, MACD, STOCH, ROC,
    ATR, BBANDS, KELTNER,
    ADX, DMI, CCI, CMF, MFI, BOP,
)


FREQS = ["daily", "hourly", "minute"]

EXPRESSIONS = [
    SMA(20), EMA(20), WMA(20), HMA(20), DEMA(20), TEMA(20),
    RSI(14), MACD(), STOCH(), ROC(14),
    ATR(14), BBANDS(), KELTNER(),
    ADX(14), DMI(14), CCI(20), CMF(20), MFI(14), BOP(14),
]


@pytest.mark.parametrize("freq", FREQS)
@pytest.mark.parametrize("expr", EXPRESSIONS, ids=str)
def test_mintalib_expressions(expr, freq, max_bars=250):
    prices = sample_prices(freq=freq, backend="polars")
    chart = Chart(prices, title="Test", max_bars=max_bars)
    chart.plot([Candlesticks(), expr])
    assert chart.count_axes() > 0
    plt.close()
