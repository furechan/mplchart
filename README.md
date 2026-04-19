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

> **Note — backend decoupling:**
> mplchart is transitioning to a backend-agnostic core. As of version 0.0.32,
> **pandas is no longer installed by default**. Choose the backend you want
> via extras: `pip install mplchart[pandas]` or `pip install mplchart[polars]`
> (or both). See the [Installation](#installation) section for details.


![Showcase Chart](/output/showcase.svg "Showcase")


## Typical Usage

```python
# Candlesticks chart with SMA, RSI and MACD indicators

import yfinance as yf

from mplchart.chart import Chart
from mplchart.primitives import Candlesticks, Volume, LinePlot
from mplchart.indicators import SMA, EMA, ROC, RSI, MACD

from mplchart.utils import normalize_prices

ticker = 'AAPL'
prices = normalize_prices(yf.Ticker(ticker).history('5y'))

Chart(prices, title=ticker, max_bars=250).plot(
    Candlesticks(),
    Volume(),
    SMA(50),
    SMA(200),
).pane("above").plot(
    RSI(14) | LinePlot(style="dashed")
).pane("below").plot(
    MACD()
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

chart = Chart(prices, title=title, max_bars=250).plot(
    Candlesticks()
).show()
```

The main drawing primitives are :
- `Candlesticks` for candlestick plots
- `OHLC` for open, high, low, close bar plots
- `Price` for price line plots
- `Volume` for volume bar plots
- `LinePlot` draw an indicator as line plot
- `AreaPlot` draw an indicator as area plot
- `BarPlot` draw an indicator as bar plot
- `ZigZag` lines between pivot points
- `Peaks` to mark peaks and valleys



## Builtin Indicators

The library includes some standard technical analysis indicators implemented in pandas/numpy.
Indicators are classes and must be instantiated as objects before being used with the plot api.

Some of the indicators included are:

- `SMA` Simple Moving Average
- `EMA` Exponential Moving Average
- `WMA` Weighted Moving Average
- `HMA` Hull Moving Average
- `ROC` Rate of Change
- `RSI` Relative Strength Index
- `ATR` Average True Range
- `NATR` Normalized Average True Range
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

Use `|` to override how an indicator is rendered, or to chain indicators:

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

Use `.apply()` to apply an indicator directly to data, or to compose indicators:

```python
SMA(50).apply(prices)          # apply indicator to data
SMA(20).apply(EMA(10))         # compose: EMA applied first, then SMA
```


## Polars Expressions

For polars-native workflows, the `expressions` subpackage provides polars `Expr` factories
as a lightweight alternative to the indicator pattern.
These can be used directly with `chart.plot()` and support all polars DataFrames.

```python
# Candlesticks chart with polars expressions

import polars as pl
from mplchart.chart import Chart
from mplchart.primitives import Candlesticks, Volume
from mplchart.expressions import SMA, EMA, RSI, MACD

Chart(prices, title=ticker, max_bars=250).plot(
    Candlesticks(),
    Volume(),
    SMA(50),
    SMA(200),
).pane("above").plot(
    RSI()
).pane("below").plot(
    MACD()
).show()
```

Expressions are plain `polars.Expr` values — they can be composed with standard polars operators,
passed to `df.select()`, or used anywhere polars expressions are accepted.

Contrary to indicators, expressions use the `@` operator to bind to a primitive:

```python
from mplchart.expressions import SMA, RSI

SMA(50) @ LinePlot(color="red")    # expression → primitive
RSI(14) @ AreaPlot(color="blue")   # expression → primitive
```


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
]

Chart(prices).plot(indicators).show()
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

Example notebooks live in the [`examples/`](examples/) folder.

**Start here:** [`typical-usage.ipynb`](examples/typical-usage.ipynb) — minimal end-to-end example.

| Topic | pandas backend | polars backend |
|---|---|---|
| Indicator / expression catalog | [`chart-indicators.ipynb`](examples/chart-indicators.ipynb) | [`chart-expressions.ipynb`](examples/chart-expressions.ipynb) |
| Display primitives & styling | [`chart-primitives-pandas.ipynb`](examples/chart-primitives-pandas.ipynb) | [`chart-primitives-polars.ipynb`](examples/chart-primitives-polars.ipynb) |

**How-to:**
- [`chart-render.ipynb`](examples/chart-render.ipynb) — render charts to SVG / PNG / JPG
- [`compare-tickers.ipynb`](examples/compare-tickers.ipynb) — overlay and rebase multiple tickers
- [`talib-examples.ipynb`](examples/talib-examples.ipynb) — use [ta-lib](https://ta-lib.github.io/ta-lib-python/) functions as indicators



## Installation

Pick the backend you want to use — pandas and polars are both optional extras:

```console
pip install mplchart[pandas]    # pandas DataFrames + indicators module
pip install mplchart[polars]    # polars DataFrames + expressions module
pip install mplchart[pandas,polars]   # both
```

A bare `pip install mplchart` installs only the backend-agnostic core
(matplotlib, numpy, pyarrow). You will need at least one of the extras
to load prices and plot indicators.

## Dependencies

Required:
- python >= 3.10
- matplotlib
- numpy
- pyarrow

Optional extras:
- `[pandas]` — enables pandas DataFrame support and the `mplchart.indicators` module
- `[polars]` — enables polars DataFrame support and the `mplchart.expressions` module


## Related Projects & Resources
- [stockcharts.com](https://stockcharts.com/) - Classic stock charts and technical analysis reference
- [mplfinance](https://pypi.org/project/mplfinance/) - Matplotlib utilities for the visualization, and visual analysis, of financial data
- [matplotlib](https://github.com/matplotlib/matplotlib) - Matplotlib: plotting with Python
- [pandas](https://github.com/pandas-dev/pandas) - Flexible and powerful data analysis / manipulation library for Python
- [polars](https://github.com/pola-rs/polars) - Fast DataFrame library for Python
- [yfinance](https://github.com/ranaroussi/yfinance) - Download market data from Yahoo! Finance's API
