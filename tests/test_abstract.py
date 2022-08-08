from mplchart.chart import Chart
from mplchart.helper import get_prices

from mplchart.primitives import Candlesticks

from talib.abstract import Function


def test_abstract():
    ticker = 'AAPL'
    prices = get_prices(ticker)

    max_bars = 250

    indicators = [
        Candlesticks(),
        Function('SMA', 50),
        Function('SMA', 200),
        Function('RSI'),
        Function('MACD'),
    ]

    chart = Chart(title=ticker, max_bars=max_bars)
    chart.plot(prices, indicators)

    assert chart.count_axes() > 1

