import pytest

from mplchart import samples
from mplchart.chart import Chart
from mplchart.primitives import Candlesticks, Volume
from mplchart.indicators import SMA, EMA, RSI, MACD, PPO, BBANDS

INDICATORS = [Volume(), SMA(50), EMA(50), RSI(), MACD(), PPO(), BBANDS()]


@pytest.fixture
def prices():
    return samples.sample_prices()


def test_prices(prices):
    assert len(prices) > 0


@pytest.mark.parametrize("indicator", INDICATORS, ids=str)
def test_chart(prices, indicator, max_bars=250):
    if indicator is None:
        indicator = SMA(50)

    indicators = [Candlesticks(), indicator]

    chart = Chart(title="Test", max_bars=max_bars)
    chart.plot(prices, indicators)

    assert chart.count_axes() > 0
