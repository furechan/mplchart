import unittest

from mplchart.chart import Chart
from mplchart.samples import sample_prices
from mplchart.primitives import Candlesticks, Volume
from mplchart.indicators import SMA, EMA, RSI, MACD, PPO, BBANDS

MAX_BARS = 250

TESTS = unittest.TestSuite()

PRICES = sample_prices()

INDICATORS = [Volume(), SMA(50), EMA(50), RSI(), MACD(), PPO(), BBANDS()]


def test_chart(indicator, count_axes: int = None):
    if indicator is None:
        indicator = SMA(50)

    indicators = [Candlesticks(), indicator]
    description = str(indicator)

    def chart_test():
        chart = Chart(title="Test", max_bars=MAX_BARS)
        chart.plot(PRICES, indicators)

        if count_axes is not None:
            assert chart.count_axes() == count_axes
        else:
            assert chart.count_axes() > 0

    test = unittest.FunctionTestCase(chart_test, description=description)
    TESTS.addTest(test)


for indicator in INDICATORS:
    test_chart(indicator)


def load_tests(loader, standard_tests, pattern):
    return TESTS
