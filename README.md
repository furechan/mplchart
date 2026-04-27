# Classic Stock Charts in Python


Create classic technical analysis stock charts in Python with minimal code.
The library is built around [matplotlib](https://github.com/matplotlib/matplotlib)
and supports both [pandas](https://github.com/pandas-dev/pandas) and [polars](https://github.com/pola-rs/polars) DataFrames.
Charts can be defined using a declarative interface,
based on a set of drawing primitives like `Candlesticks`, `Volume`
and technical indicators like `SMA`, `EMA`, `RSI`, `ROC`, `MACD`, etc ...



> **Warning:**
> This project is experimental and the interface is likely to change.
> For a related project with a mature api you may want to look into
> [mplfinance](https://pypi.org/project/mplfinance/).


![Showcase Chart](/output/showcase.svg "Showcase")


## Typical Usage

```python
# Candlesticks chart with SMA, RSI and MACD indicators

import yfinance as yf

from mplchart.chart import Chart
from mplchart.primitives import Candlesticks, Volume, Pane, LinePlot
from mplchart.indicators import SMA, RSI, MACD

from mplchart.utils import normalize_prices

ticker = 'AAPL'
prices = normalize_prices(yf.Ticker(ticker).history('5y'))

Chart(prices, title=ticker, max_bars=250).plot(
    Candlesticks(), Volume(), SMA(50), SMA(200),
    Pane("above", yticks=(30, 50, 70)),
    RSI(14) | LinePlot(overbought=70, oversold=30),
    Pane("below"),
    MACD(),
).show()
```


## Conventions

Prices data is expected to be a pandas or polars DataFrame
with columns `open`, `high`, `low`, `close`, `volume`
and a datetime column named `date` or `datetime` (or a datetime index for pandas).

> **Note:** `Chart` and all indicators require lowercase column names.
> Use `normalize_prices` from `mplchart.utils` to normalize your DataFrame before use:
>
> ```python
> from mplchart.utils import normalize_prices
> prices = normalize_prices(yf.Ticker(ticker).history('5y'))
> ```



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
- `Price` for price line plots
- `Volume` for volume bar plots
- `Pane` to switch to a different pane (above or below)
- `LinePlot` draw an indicator as line plot
- `AreaPlot` draw an indicator as area plot
- `BarPlot` draw an indicator as bar plot
- `ZigZag` lines between pivot points
- `Peaks` to mark peaks and valleys
- `HLine` to draw a horizontal reference line on the current pane
- `VLine` to draw a vertical line across all panes at a given date



## Builtin Indicators

The library includes some standard technical analysis indicators for **pandas** DataFrames.
Indicators are classes and must be instantiated as objects before being used with the plot api.

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
- `MIDPRICE` Midpoint Price
- `TYPPRICE` Typical Price
- `WCLPRICE` Weighted Close Price

Use `|` to bind an indicator to a rendering primitive, or to compose indicators:

```python
SMA(50) | LinePlot(style="dashed", color="red")   # bind indicator to primitive
SMA(50) | ROC(1)                                   # chain indicators
```

```python
# Customizing indicator style with LinePlot

from mplchart.indicators import SMA, EMA, ROC
from mplchart.primitives import Candlesticks, LinePlot

indicators = [
    Candlesticks(),
    SMA(20) | LinePlot(style="dashed", color="red", alpha=0.5, width=3)
]

Chart(prices).plot(indicators)
```

If the indicator returns a DataFrame instead of a Series, specify an `item` (column name) in the primitive.

Use `prices | indicator` to apply an indicator directly to data:

```python
prices | SMA(50)               # apply indicator to data
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
    RSI() @ LinePlot(overbought=70, oversold=30),
    Pane("below"),
    MACD(),
).show()
```

Expressions are plain `polars.Expr` values — they can be composed with standard polars operators,
passed to `df.select()`, or used anywhere polars expressions are accepted.

Contrary to indicators, expressions use the `@` operator to bind to a primitive:

```python
from mplchart.primitives import LinePlot, AreaPlot
from mplchart.expressions import SMA, RSI

SMA(50) @ LinePlot(color="red")    # expression → primitive
RSI(14) @ AreaPlot(color="blue")   # expression → primitive
```


## Talib Functions

If you have `ta-lib` installed you can use its abstract functions as indicators. They are created by calling `Function` with the name of the function and its parameters. Ta-lib functions work with both pandas and polars backends.

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

Example notebooks live in the [`examples/`](examples/) folder — see the [examples README](examples/README.md) for the full list.



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


## Related Projects & Resources
- [stockcharts.com](https://stockcharts.com/) - Classic stock charts and technical analysis reference
- [mplfinance](https://pypi.org/project/mplfinance/) - Matplotlib utilities for the visualization, and visual analysis, of financial data
- [matplotlib](https://github.com/matplotlib/matplotlib) - Matplotlib: plotting with Python
- [pandas](https://github.com/pandas-dev/pandas) - Flexible and powerful data analysis / manipulation library for Python
- [polars](https://github.com/pola-rs/polars) - Fast DataFrame library for Python
- [yfinance](https://github.com/ranaroussi/yfinance) - Download market data from Yahoo! Finance's API
