from mplchart.chart import Chart

from mplchart.primitives import Candlesticks, Volume
from mplchart.indicators import SMA, RSI, MACD


def test_chart(prices):
    max_bars = 250
    indicators = [Candlesticks(), SMA(50), SMA(200), Volume(), RSI(), MACD()]

    chart = Chart(title="Test", max_bars=max_bars)
    chart.plot(prices, indicators)

    assert chart.count_axes() > 1

