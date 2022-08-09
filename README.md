# Classic Stock Charts in Python


This project aims at creating classic
technical analysis stock charts in Python with minimum code.
The library is built around the excellent 
[matplotlib](https://github.com/matplotlib/matplotlib).  
The interface is declarative, based on a set of drawing primitives
like `Candleststicks`, `Volume`, `Peaks`
and technical indicators
like `SMA`, `EMA`, `RSI`, `ROC`, `MACD`, etc ...
If you have [ta-lib](https://github.com/mrjbq7/ta-lib)
installed you can also use its abstract functions as indicators but it is not a requirement.


![Showcase Chart](/output/showcase.svg "Showcase")


## Warning

This is work in progress! For any serious usage you may want to you look into projects
like [mplfinance](https://pypi.org/project/mplfinance/).


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
with columns `open`, `high`, `low`, `close` `volume` in **lower case**
and a timestamp index named `date`.

For testing purposes you can use the `helper` module
which can fetch sample prices in the proper format via
[yfinance](https://github.com/ranaroussi/yfinance).
This is meant to be used for testing/demo purposes only!
See yfinance for more information on its usage.

```python
from mplchart.helper import get_prices

ticker = 'AAPL'
freq = 'daily'
prices = get_prices(ticker, freq=freq)
```

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
The main drawing primitives are :
- `Candlesticks` for candlesticks plots
- `OHLC` for open, high, low, close bar plots
- `Price` for price line plots
- `Volume` for volume bar plots
- `Peaks` to plot peaks and valleys
- `SameAxes` to force plot on the same axes
- `NewAxes` to force plot on a new axes

See example notebook [mplchart-primitives.ipynb](/examples/mplchart-primitives.ipynb) 

## Builtin Indicators

The libary contains some basic technical analysis indicators implemented in pandas/numpy.
All indicators are classes that must be instantiated
before being used in the plot api.
Some of the indicators included are:
- `SMA` Simple Moving Average
- `EMA` Exponential Moving Average
- `ROC` Rate of Change
- `RSI` Relative Strength Index
- `MACD` Moving Average Convergence Divergence
- `PPO` Price Percentage Oscillator 
- `SLOPE` Slope (linear regression with time)
- `BBANDS` Bolling Bands

See example notebook [mplchart-builtins.ipynb](/examples/mplchart-builtins.ipynb) 

## Ta-lib Abstract Functions

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
 
See example notebook [mplchart-abstract.ipynb](/examples/mplchart-abstract.ipynb) 


## Custom Indicators

It is easy to create custom indicators.
An indicator is basically a callable that takes a prices data frame and returns a series as result.
A function can be used as an indicator but we suggest you implement indicators as a callable dataclass.

```python
from dataclasses import dataclass

from mplchart.library import get_series, calc_ema

@dataclass
class DEMA:
    """ Double Exponential Moving Average """
    period: int = 20

    same_scale = True
    # same_scale is an optional class attribute that indicates
    # the indicator should be plot on the same axes by default

    def __call__(self, prices):
        series = get_series(prices)
        ema1 = calc_ema(series, self.period)
        ema2 = calc_ema(ema1, self.period)
        return 2 * ema1 - ema2

```

See example notebook [mplchart-custom.ipynb](/examples/mplchart-custom.ipynb) 


## Example Notebooks

You can find example notebooks in the [examples](/examples/) folder. 

- [mplchart-primitives.ipynb](/examples/mplchart-primitives.ipynb) A quick tour of the drawing primitives 
- [mplchart-builtins.ipynb](/examples/mplchart-builtins.ipynb) A quick tour of the builtin indicators 
- [mplchart-abstract.ipynb](/examples/mplchart-abstract.ipynb) Using ta-lib abstract functions as indicators 


## Developer Notes

You can install this package with pip


```console
pip install git+ssh://git@github.com/furechan/mplchart-proto.git
```

## Requirements:

- python >= 3.8
- matplotlib
- pandas
- numpy
- yfinance


## Related Projects & Resources
- [stockcharts.com](https://stockcharts.com/) Beautiful Stock Charts and Technical Analysis Reference
- [mplfinance](https://pypi.org/project/mplfinance/) Matplotlib utilities for the visualization,
and visual analysis, of financial data
- [matplotlib](https://github.com/matplotlib/matplotlib) Matplotlib: plotting with Python
- [yfinance](https://github.com/ranaroussi/yfinance) Download market data from Yahoo! Finance's API
- [ta-lib](https://github.com/mrjbq7/ta-lib) Python wrapper for TA-Lib
- [pandas](https://github.com/pandas-dev/pandas) Flexible and powerful data analysis / manipulation library
for Python, providing labeled data structures similar to R data.frame objects,
statistical functions, and much more
- [numpy](https://github.com/numpy/numpy) The fundamental package for scientific computing with Python
