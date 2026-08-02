""" mplchart with streamlit demo """

import streamlit as st
import yfinance as yf

from mplchart.chart import Chart
from mplchart.primitives import Candlesticks, Volume
from mplchart.indicators import SMA
from mplchart.utils import normalize_prices

ticker = 'AAPL'
prices = normalize_prices(yf.Ticker(ticker).history('5y'))

st.dataframe(prices.tail())

max_bars = 250

indicators = [
    Candlesticks(), SMA(50), SMA(200), Volume(),
]

chart = Chart(prices, title=ticker, max_bars=max_bars)
chart.plot(indicators)

st.pyplot(chart.figure)

