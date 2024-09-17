""" mplchart with streamlit example """

import streamlit as st
import yfinance as yf

from mplchart.chart import Chart
from mplchart.primitives import Candlesticks, Volume
from mplchart.indicators import SMA, RSI, MACD

ticker = 'AAPL'
prices = yf.Ticker(ticker).history('5y')

st.dataframe(prices.tail())

max_bars = 250

indicators = [
    Candlesticks(), SMA(50), SMA(200), Volume(),
    RSI(),
    MACD(),
]

chart = Chart(title=ticker, max_bars=max_bars)
chart.plot(prices, indicators)

st.pyplot(chart.figure)

