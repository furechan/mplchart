# Classic Stock Charts in Python


Create classic technical analysis stock charts in Python with minimal code.
The library is built around [matplotlib](https://github.com/matplotlib/matplotlib)
and supports both [pandas](https://github.com/pandas-dev/pandas)
and [polars](https://github.com/pola-rs/polars) DataFrames.
Charts can be defined using a declarative interface,
based on a set of drawing primitives like `Candlesticks`, `Volume`
and technical indicators like `SMA`, `EMA`, `RSI`, `ROC`, `MACD`, etc ...

📖 **Documentation**: tutorials and a chart gallery at [furechan.github.io/mplchart](https://furechan.github.io/mplchart/)



> [!WARNING]
> This project is experimental and the interface is likely to change.
> For a related project with a mature api you may want to look into [mplfinance](https://pypi.org/project/mplfinance/).


![Showcase Chart](https://github.com/furechan/mplchart/raw/main/docs/assets/showcase.svg "Showcase")


## Typical Usage

```python
# Candlesticks chart with SMA, RSI and MACD indicators

import yfinance as yf

from mplchart.chart import Chart
from mplchart.primitives import Candlesticks, Volume, Pane, LinePlot
from mplchart.indicators import SMA, RSI, MACD

ticker = 'AAPL'
prices = yf.Ticker(ticker).history('5y')

Chart(prices, title=ticker, max_bars=250, normalize=True).plot(
    Candlesticks(), Volume(), SMA(50), SMA(200),
    Pane("above", yticks=(30, 50, 70)),
    LinePlot(RSI(14), overbought=70, oversold=30),
    Pane("below"),
    MACD(),
).show()
```


## Styles

Charts are styled via the `style=` option — a builtin style, any matplotlib stylesheet name, or a custom style dict. Styles are total: ambient matplotlib settings never affect a chart.

```python
from mplchart.styles import available_styles

available_styles()
# ['chartist', 'modern', 'mplchart', 'nightclouds']

# builtin style
Chart(prices, title=ticker, style="nightclouds").plot(Candlesticks()).show()

# any matplotlib stylesheet
Chart(prices, title=ticker, style="ggplot").plot(Candlesticks()).show()

# custom style dict
MY_STYLE = {
    "stylesheet": "dark_background",
    "settings": {
        "candle.up.color": "#26a69a",
        "candle.down.color": "#ef5350",
    },
}
Chart(prices, title=ticker, style=MY_STYLE).plot(Candlesticks()).show()
```

## Conventions

Prices data is expected to be a dataframe with columns `open`, `high`, `low`, `close`, `volume` in **lower case** and a datetime column named `date` or `datetime` (or a datetime index for pandas). 
If your data has column names in different capitalization (like data from yfinance) use the `normalize` option `Chart(..., normalize=True)` or call `normalize_prices` explicitely to normalize the dataframe.

```python
# Normalize prices to lower case column names

import yfinance as yf
from mplchart.utils import normalize_prices

prices = normalize_prices(yf.Ticker(ticker).history('5y'))
```



## Drawing Primitives

The library contains drawing primitives that can be used like an indicator in the plot api.
Primitives are classes and must be instantiated as objects before being used with the plot api.

```python
# Candlesticks chart 

from mplchart.chart import Chart
from mplchart.primitives import Candlesticks

Chart(prices, title=title, max_bars=250).plot(
    Candlesticks()
).show()
```

The main drawing primitives are :
- `Candlesticks` for candlestick plots
- `OHLC` for open, high, low, close bar plots
- `Volume` for volume bar plots
- `Pane` to switch to a different pane (above or below)
- `LinePlot` draw an indicator as line plot
- `AreaPlot` draw an indicator as area plot
- `BarPlot` draw an indicator as bar plot
- `Stripes` to shade background areas where a condition is active
- `Markers` to mark signal crossings with symbols
- `ZigZag` lines between pivot points
- `Swings` to mark local peaks and valleys (swing highs/lows)
- `TrendLines` to fit support and resistance trend lines (experimental)
- `HLine` to draw a horizontal reference line on the current pane
- `VLine` to draw a vertical line across all panes at a given date



## Builtin Indicators

The library includes some standard technical analysis indicators for **pandas** DataFrames.
Indicators are classes and must be instantiated as objects before being used with the plot api.
Instantiated they are callables, you can apply them like calling a function `SMA(50)(prices)`.

Some of the indicators included are:

- `SMA` Simple Moving Average
- `EMA` Exponential Moving Average
- `WMA` Weighted Moving Average
- `HMA` Hull Moving Average
- `RMA` Rolling Moving Average (Wilder's)
- `DEMA` Double Exponential Moving Average
- `TEMA` Triple Exponential Moving Average
- `MOM` Momentum
- `ROC` Rate of Change
- `RSI` Relative Strength Index
- `ADX` Average Directional Index
- `DMI` Directional Movement Index
- `MACD` Moving Average Convergence Divergence
- `PPO` Price Percentage Oscillator
- `BOP` Balance of Power
- `CMF` Chaikin Money Flow
- `MFI` Money Flow Index
- `STOCH` Stochastic Oscillator
- `TRANGE` True Range
- `ATR` Average True Range
- `NATR` Normalized Average True Range
- `BBANDS` Bollinger Bands
- `BBP` Bollinger Bands Percent
- `BBW` Bollinger Bands Width
- `KELTNER` Keltner Channel
- `DONCHIAN` Donchian Channel
- `MEDPRICE` Median Price
- `TYPPRICE` Typical Price
- `WCLPRICE` Weighted Close Price
- `AVGPRICE` Average Price

Pass an indicator to a rendering primitive to customize display — the `@` binding operator is an equivalent alternative:


```python
# Customizing indicator style with LinePlot

from mplchart.indicators import SMA, EMA, ROC
from mplchart.primitives import Candlesticks, LinePlot

indicators = [
    Candlesticks(),
    LinePlot(SMA(20), style="dashed", color="red", alpha=0.5, width=3)
]

Chart(prices).plot(indicators)
```


## Polars Expressions

For **polars** DataFrames, the `expressions` subpackage provides polars `Expr` factories
as an alternative to the indicator pattern.
These can be used directly with `chart.plot()`.

```python
# Candlesticks chart with polars expressions

from mplchart.chart import Chart
from mplchart.primitives import Candlesticks, Volume, Pane, LinePlot
from mplchart.expressions import SMA, EMA, RSI, MACD

Chart(prices, title=ticker, max_bars=250).plot(
    Candlesticks(), Volume(), SMA(50), SMA(200),
    Pane("above", yticks=(30, 50, 70)),
    LinePlot(RSI(), overbought=70, oversold=30),
    Pane("below"),
    MACD(),
).show()
```

Expressions are plain `polars.Expr` values — they can be composed with standard polars operators,
passed to `df.select()`, or used anywhere polars expressions are accepted.

Pass an expression to a rendering primitive to customize display — the `@` binding operator is an equivalent alternative:

```python
from mplchart.primitives import LinePlot, AreaPlot
from mplchart.expressions import SMA, RSI

LinePlot(SMA(50), color="red")     # expression → primitive
AreaPlot(RSI(14), color="blue")    # expression → primitive
SMA(50) @ LinePlot(color="red")    # operator form
```


## Talib Functions

If you have ta-lib installed you can use its abstract functions as indicators. They are created by calling the `Function` factory with the name of the function and its parameters. Ta-lib functions work with both pandas and polars backends.

```python
# Candlesticks chart with talib functions

from mplchart.primitives import Candlesticks
from talib.abstract import Function

indicators = [
    Candlesticks(),
    Function('SMA', 50),
    Function('SMA', 200),
]

Chart(prices).plot(indicators).show()
```

## Examples

Example notebooks live in the `examples` folder.


## Installation

```console
pip install mplchart
```

The indicators module requires pandas; the expressions module requires polars.
If either is already in your environment, mplchart will use it automatically.
The `[pandas]`, `[polars]`, and `[all]` extras are just a convenience — they
install pandas or polars alongside mplchart, nothing more:

```console
pip install mplchart[pandas]
pip install mplchart[polars]
pip install mplchart[all]
```

## Dependencies

Required:
- python >= 3.10
- matplotlib
- numpy
- pyarrow

Optional extras:
- `[pandas]` — pandas
- `[polars]` — polars
- `[all]` — pandas and polars


## Related Projects
- [mplfinance](https://pypi.org/project/mplfinance/) - Matplotlib utilities for the visualization, and visual analysis, of financial data
- [cufflinks](https://github.com/santosjorge/cufflinks) - Productivity Tools for Plotly + Pandas
- [matplotlib](https://github.com/matplotlib/matplotlib) - Matplotlib: plotting with Python
- [pandas](https://github.com/pandas-dev/pandas) - Flexible and powerful data analysis / manipulation library for Python
- [polars](https://github.com/pola-rs/polars) - Fast DataFrame library for Python
- [yfinance](https://github.com/ranaroussi/yfinance) - Download market data from Yahoo! Finance's API
