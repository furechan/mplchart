""" sample script to display a chart """

import yfinance as yf

from mplchart.chart import Chart

from mplchart.primitives import Candlesticks, Volume
from mplchart.indicators import SMA, RSI, MACD


def main():
    ticker = "AAPL"
    prices = yf.Ticker(ticker).history(period="5y")

    max_bars = 250
    indicators = [Candlesticks(), SMA(50), SMA(200), Volume(), RSI(), MACD()]
    chart = Chart(title=ticker, max_bars=max_bars)
    chart.plot(prices, indicators)
    chart.show()


if __name__ == "__main__":
    main()
