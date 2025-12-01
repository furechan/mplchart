import marimo

__generated_with = "0.18.1"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import yfinance as yf

    from mplchart.chart import Chart
    from mplchart.primitives import Candlesticks, Volume
    from mplchart.indicators import SMA, RSI, MACD

    import matplotlib.pyplot as plt
    return Candlesticks, Chart, MACD, RSI, SMA, Volume, mo, plt, yf


@app.cell
def _(mo):
    ticker = mo.ui.text(value="AAPL", label="Ticker", on_change=None)
    ticker
    return (ticker,)


@app.cell
def _(Candlesticks, Chart, MACD, RSI, SMA, Volume, plt, ticker, yf):
    prices = yf.Ticker(ticker.value).history(period="5y")

    title = str(ticker.value)
    indicators = [Candlesticks(), Volume(), SMA(50), SMA(200), RSI(), MACD()]
    max_bars = 250

    chart = Chart(title=title, max_bars=max_bars)
    chart.plot(prices, indicators)
    plt.show()
    return


if __name__ == "__main__":
    app.run()
