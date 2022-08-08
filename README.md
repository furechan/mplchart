# Classic Stock Charts in Python

This project aims at creating classic
technical analysis stock charts in Python.
The library is built around the excellent 
[matplotlib](https://github.com/matplotlib/matplotlib)
and depends otherwize only on
[pandas](https://github.com/pandas-dev/pandas). If you have
[ta-lib](https://github.com/mrjbq7/ta-lib)
installed you can also use its abstract functions as indicators but it is not a requirement. 
The interface is declarative, based on a set of drawing primitives
like `Candleststicks`, `Volume`, `Peaks`
and technical indicators
like `SMA`, `EMA`, `RSI`, `ROC`, `MACD`, etc ...


![Showcase Chart](/output/showcase.svg "Showcase")

## Warning

This project is experimental! For any serious usage you may want to you look into
[mplfinance](https://pypi.org/project/mplfinance/).

## Requirements

- Python >= 3.8
- matplotlib
- pandas
- yfinance


## Typical Usage

```python
from mplchart.chart import Chart
from mplchart.helper import get_prices
from mplchart.primitives import Candlesticks, Volume
from mplchart.indicators import ROC, SMA, EMA, RSI, MACD

ticker = 'AAPL'
freq = 'daily'
prices = get_prices(ticker, freq=freq)

max_bars = 250

indicators = [
    Candlesticks(), SMA(50), SMA(200), Volume(),
    RSI(),
    MACD(),
]

chart = Chart(title=ticker, max_bars=max_bars)
chart.plot(prices, indicators)
```

## Conventions

Prices are expected to be stored as a pandas DataFrame
with columns
`open`, `high`, `low`, `close` `volume`
and a timestamp index 
named `date`.

For testing purposes you can use the `helper` module
which can fetch sample prices in the proper format via
[yfinance](https://github.com/ranaroussi/yfinance).
**This is meant to be used for testing/demo purposes only!**
See yfinance for more information on its usage.

```python
from mplchart.helper import get_prices

ticker = 'AAPL'
freq = 'daily'
prices = get_prices(ticker, freq=freq)
```

See example notebook
[mplchart-helper.ipynb](/examples/mplchart-helper.ipynb)

## Drawing Primitives

The library contains drawing primitives that can be used as an indicator in the plot api.
All primitives are classes that must be instantiated as objects before being used in the plot api.
Here is a snippet for the `Candlesticks` primitive.

```python
from mplchart.primitives import Candlesticks

indicators = [Candlesticks()]
chart = Chart(title=title, max_bars=max_bars)
chart.plot(prices, indicators)
```
The main primitives are :
- `Candlesticks` for candlesticks plots
- `OHLC` for Open High Low Close bar plots
- `Price` for price line plots
- `Volume` for volume bar plots

See example notebook
[mplchart-primitives.ipynb](/examples/mplchart-primitives.ipynb)

## Builtin Indicators

The libary contains some basic technical analysis indicators implemented in pandas.
All indicators are classes that must be instantiated
before being used in the plot api. Some of the indicators included are:
- `SMA` imple Moving Average
- `EMA` Exponential Moving Average
- `ROC` Rate of Change
- `RSI` Relative Strenght Index
- `MACD` Mooving Average Convergence Divergence

See example notebook
[mplchart-builtins.ipynb](/examples/mplchart-builtins.ipynb)

## Ta-lib Functions

If you have 
[ta-lib](https://github.com/mrjbq7/ta-lib)
installed you can use its abstract functions as indicators.
The functions are created by calling `abstract.Function` with the name of the indicator and its parameters.

```python
from talib.abstract import Function

indicators = [
    Candlesticks(),
    Function('SMA', 50),
    Function('SMA', 200),
    Function('RSI'),
    Function('MACD'),
]
```

See example notebook
[mplchart-abstract.ipynb](/examples/mplchart-abstract.ipynb)


## Example Notebooks

- [mplchart-primitives.ipynb](/examples/mplchart-primitives.ipynb) A quick tour of the drawing primitives 
- [mplchart-builtins.ipynb](/examples/mplchart-builtins.ipynb) A quick tour of the builtin indicators 
- [mplchart-abstract.ipynb](/examples/mplchart-abstract.ipynb) Using ta-lib abstract functions as indicators 



## Developer Notes

You can install the module with pip

```console
pip install git+ssh://git@github.com/furechan/mplchart-proto.git
```

## Related Projects & Resources
- [StockCharts.com](https://stockcharts.com/) Better Charting. Smarter Investing.
- [mplfinance](https://pypi.org/project/mplfinance/) Matplotlib utilities for the visualization,
and visual analysis, of financial data
- [matplotlib](https://github.com/matplotlib/matplotlib) matplotlib: plotting with Python
- [pandas](https://github.com/pandas-dev/pandas) Flexible and powerful data analysis / manipulation library
for Python, providing labeled data structures similar to R data.frame objects,
statistical functions, and much more
- [yfinance](https://github.com/ranaroussi/yfinance) Download market data from Yahoo! Finance's API
