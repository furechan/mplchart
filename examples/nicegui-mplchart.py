""" sample script to display a chart with nicegui """

from nicegui import ui

import yfinance as yf

from matplotlib import pyplot as plt

from mplchart.chart import Chart
from mplchart.primitives import Candlesticks, Volume
from mplchart.indicators import SMA, RSI, MACD

symbol = "AAPL"
period = "25Y"
max_bars = 250

with ui.row():
    ticker = ui.input('Ticker', value=symbol)
    button = ui.button('Update Chart')

with ui.pyplot(figsize=(9, 6), close=False) as plot:
    plt.plot()


def update_chart():
    prices = yf.Ticker(ticker.value).history(period=period, auto_adjust=True)
    indicators = [Candlesticks(), SMA(50), SMA(200), Volume(), RSI(), MACD()]

    with plot:
        chart = Chart(title=ticker.value, max_bars=max_bars, figure=plot.fig)
        chart.plot(prices, indicators)
        ui.update(plot)


update_chart()

ticker.on("keydown.enter", update_chart)
button.on("click", update_chart)

ui.run()
