# Classic Stock Charts in Python


Create classic technical analysis stock charts in Python with minimal code.
The library is built around [matplotlib](https://github.com/matplotlib/matplotlib)
and [pandas](https://github.com/pandas-dev/pandas). 
Charts can be defined using a declarative interface,
based on a set of drawing primitives like `Candleststicks`, `Volume`
and technical indicators like `SMA`, `EMA`, `RSI`, `ROC`, `MACD`, etc ...


> **Warning**
> This project is experimental and the interface can change.
> For a similar project with a mature api you may want to look into
> [mplfinance](https://pypi.org/project/mplfinance/).


![Showcase Chart](https://github.com/furechan/mplchart/raw/main/output/showcase.svg "Showcase")


## Typical Usage

```python
# Candlesticks chart with SMA, RSI and MACD indicators

import yfinance as yf

from mplchart.chart import Chart
from mplchart.primitives import Candlesticks, Volume
from mplchart.indicators import SMA, EMA, ROC, RSI, MACD

ticker = 'AAPL'
prices = yf.Ticker(ticker).history('5y')

max_bars = 250

indicators = [
    Candlesticks(),
    Volume(),
    SMA(50),
    SMA(200),
    RSI(),
    MACD(),
]

chart = Chart(title=ticker, max_bars=max_bars)
chart.plot(prices, indicators)
chart.show()
```


## Conventions

Prices data is expected to be presented as a pandas DataFrame
with columns `open`, `high`, `low`, `close` `volume`
and a datetime index named `date` or `datetime`.

Even though the chart object automatically converts price
column names to lower case before calling any indicator,
if you intend on using indicators independently from the chart object,
you must use prices dataframes with all lower case column names!



## Drawing Primitives

The library contains drawing primitives that can be used like an indicator in the plot api.
Primitives are classes and must be instantiated as objects before being used with the plot api.

```python
# Candlesticks chart 

from mplchart.chart import Chart
from mplchart.primitives import Candlesticks

indicators = [Candlesticks()]
chart = Chart(title=title, max_bars=max_bars)
chart.plot(prices, indicators)
```

The main drawing primitives are :
- `Candlesticks` for candlestick plots
- `OHLC` for open, high, low, close bar plots
- `Price` for price line plots
- `Volume` for volume bar plots
- `Peaks` to mark peaks and valleys
- `SameAxes` to use same axes as last plot
- `NewAxes` to use new axes above or below
- `LinePlot` draw an indicator as line plot
- `AreaPlot` draw an indicator as area plot
- `BarPlot` draw an indicator as bar plot
- `ZigZag` lines between pivot points




## Builtin Indicators

The libary includes some standard technical analysis indicators implemented in pandas/numpy.
Indicators are classes and must be instantiated as objects before being used with the plot api.

Some of the indicators included are:

- `SMA` Simple Moving Average
- `EMA` Exponential Moving Average
- `WMA` Weighted Moving Average
- `HMA` Hull Moving Average
- `ROC` Rate of Change
- `RSI` Relative Strength Index
- `ATR` Average True Range
- `ATRP` Average True Range Percent
- `ADX` Average Directional Index
- `DMI` Directional Movement Index
- `MACD` Moving Average Convergence Divergence
- `PPO` Price Percentage Oscillator 
- `CCI` Commodity Channel Index
- `BOP` Balance of Power
- `CMF` Chaikin Money Flow
- `MFI` Money Flow Index
- `SLOPE` Slope (linear regression)
- `STOCH` Stochastic Oscillator
- `BBANDS` Bollinger Bands
- `KELTNER` Keltner Channel
- `DEMA` Double Exponential Moving Average
- `TEMA` Triple Exponential Moving Average


## Talib Indicators

If you have `ta-lib` installed you can use its abstract functions as indicators. The indicators are created by calling `Function` with the name of the indicator and its parameters.

```python
# Candlesticks chart with talib indicators

from mplchart.primitives import Candlesticks
from talib.abstract import Function

indicators = [
    Candlesticks(),
    Function('SMA', 50),
    Function('SMA', 200),
    Function('RSI'),
    Function('MACD'),
]
```

## Override indicator rendering with the plotting primitives

Most indicators are drawn as line plots with default colors and settings. You can override the rendering of an indicator by piping it with the `|` operator into a primitive like `LinePlot`, `AreaPlot` or `BarPlot` as in the example below. If the indicator returns a dataframe instead of a series you need to specify an `item` (column name) in the primitive.


```python
# Customizing indicator style with LinePlot

from mplchart.indicators import SMA, EMA, ROC
from mplchart.primitives import Candlesticks, LinePlot

indicators = [
    Candlesticks(),
    SMA(20) | LinePlot(style="dashed", color="red", alpha=0.5, width=3)
]
```


## Override target axes with `NewAxes` and `SameAxes` primitives

Indicators usually plot in a new axes below, except for a few indicators that plot by default in the main axes. You can change the target axes for any indicator by piping it into an axes primitive as in the example below.

```python
# Plotting two indicators on the same axes with SameAxes primitive

from mplchart.indicators import SMA, EMA, ROC
from mplchart.primitives import Candlesticks, SameAxes

indicators = [
    Candlesticks(),
    ROC(20),
    ROC(50) | SameAxes(),
]
```


## Custom Indicators

Any callable that accepts a prices dataframe and returns a series or dataframe can be used as an indicator.
You can also implement a custom indicator as a subclass of `Indicator`.

```python
# Custom Indicator Example

from mplchart.model import Indicator
from mplchart.library import calc_ema

class DEMA(Indicator):
    """Double Exponential Moving Average"""

    same_scale: bool = True
    # boolean, whether the indicator can be drawn
    # on the same axes as the prices

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        ema1 = calc_ema(series, self.period)
        ema2 = calc_ema(ema1, self.period)
        return 2 * ema1 - ema2
```


## Examples

You can find example notebooks and scripts in the `examples` folder. 

## Installation

You can install this package with pip

```console
pip install mplchart
```

## Dependencies

- python >= 3.9
- matplotlib
- pandas
- numpy


## Related Projects & Resources
- [stockcharts.com](https://stockcharts.com/) Classic stock charts and technical analysis reference
- [mplfinance](https://pypi.org/project/mplfinance/) Matplotlib utilities for the visualization, and visual analysis, of financial data
- [matplotlib](https://github.com/matplotlib/matplotlib) Matplotlib: plotting with Python
- [pandas](https://github.com/pandas-dev/pandas) Flexible and powerful data analysis / manipulation library for Python
- [yfinance](https://github.com/ranaroussi/yfinance) Download market data from Yahoo! Finance's API
