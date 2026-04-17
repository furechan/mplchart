"""Indicator tests"""

import pytest
import matplotlib.pyplot as plt

pytest.importorskip("pandas")
pytestmark = pytest.mark.pandas

from mplchart.chart import Chart  # noqa: E402
from mplchart.samples import sample_prices  # noqa: E402
from mplchart.primitives import Candlesticks, Volume  # noqa: E402
from mplchart.indicators import (  # noqa: E402
    SMA, EMA, WMA, HMA, TSF,
    RSI, ATR, NATR, ADX,
    MACD, PPO, SLOPE,
    BBANDS, STOCH, CMF, BOP, MFI,
)


FREQS = ["daily", "hourly", "minute"]

INDICATORS = [
    Volume(),
    SMA(20),
    EMA(20),
    WMA(20),
    HMA(20),
    TSF(20),
    RSI(),
    ATR(),
    NATR(),
    ADX(),
    MACD(),
    PPO(),
    SLOPE(),
    BBANDS(),
    STOCH(),

    CMF(),
    BOP(),
    MFI(),
]


@pytest.mark.parametrize("freq", FREQS)
def test_prices(freq):
    prices = sample_prices(freq=freq)
    assert len(prices) > 0


@pytest.mark.parametrize("freq", FREQS)
@pytest.mark.parametrize("indicator", INDICATORS, ids=str)
def test_indicators(indicator, freq, max_bars=250):
    prices = sample_prices(freq=freq)
    chart = Chart(prices, title="Test", max_bars=max_bars)
    chart.plot([Candlesticks(), indicator])
    assert chart.count_axes() > 0
    plt.close()
