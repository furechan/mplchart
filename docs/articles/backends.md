# Pandas and polars backends

mplchart works with both pandas and polars DataFrames. You pass whichever you have to `Chart(prices)`, and the charting layer — primitives, panes, styling, rendering — behaves identically. This page explains what is shared, what differs, and how to choose.

## What is shared

The chart itself is backend-agnostic. When you create a `Chart`, the prices frame is wrapped in a backend-native *data view* that handles slicing, date mapping, and evaluation — everything downstream (candlesticks, panes, reference lines, rendering to SVG/PNG) is common code. Neither pandas nor polars is a hard dependency of the package; install the one you use:

```bash
pip install mplchart[pandas]     # or mplchart[polars], or mplchart[all]
```

Data conventions are also shared: columns `open`, `high`, `low`, `close`, `volume` in lower case, and a datetime column named `date` or `datetime` (or a datetime index for pandas). Use `Chart(..., normalize=True)` for data with different capitalization, like yfinance output.

## Existing columns or deferred calculations

On either backend, `chart.plot("sma-20")` reads the `sma-20` column from `prices`. Your data pipeline can compute that column before creating the chart:

With pandas:

```python
prices["sma-20"] = prices["close"].rolling(20).mean()

```

With polars:

```python
import polars as pl

prices = prices.with_columns(pl.col("close").rolling_mean(20).alias("sma-20"))
```

In either case, plot with `Chart(prices).plot(Candlesticks(), "sma-20")`, importing the chart and primitives as usual.

Alternatively, `chart.plot(SMA(20))` defers calculation from `prices` until plotting. Both column names and calculations use default rendering, with a line for a single column or moving average. Renderer primitives are optional: use `Line("sma-20", color="red")` or `Line(SMA(20), color="red")` to customize the display. `SMA(20) @ Line()` is equivalent to `Line(SMA(20))`; the binding syntax does not determine when calculation happens. Both paths use the same renderers. The backend-specific indicator and expression systems below are conveniences for deferred calculations.

Pandas expressions (`pd.col(...)` or `.as_expr()`) must use constructor binding, such as `Stripes(RSI(14).as_expr() < 30)`: pandas captures `@` itself. Polars expressions support both binding forms, including composed expressions such as `(EMA(20) - EMA(50)) @ Area()`.

## What differs: computing values

The one real difference between the backends is how *computed series* — moving averages, oscillators, custom formulas — are expressed:

| | pandas | polars |
|---|---|---|
| Module | `mplchart.indicators` | `mplchart.expressions` |
| `SMA(50)` returns | an `Indicator` object (callable on prices) | a native `pl.Expr` |
| Composition | `EMA(20) \| ROC(1)` (chaining) | `ROC(1, src=EMA(20))` (nesting) |
| Boolean conditions | `RSI(14).as_expr() < 30` | `RSI(14) < 30` (native) |
| Custom computations | plain function or `Indicator` subclass | any `pl.Expr`, or a `wrap_expression` factory |
| Apply outside a chart | `prices.pipe(SMA(50))` | `prices.select(SMA(50))` |

The built-in names match on both sides — `SMA`, `EMA`, `RSI`, `MACD`, `BBANDS`, and the rest — and their outputs are tested for parity between backends. A chart definition like `Chart(prices).plot(Candlesticks(), SMA(50)).pane("below").plot(RSI(14))` reads the same either way; only the import line reveals the backend.

The mechanics of each system are covered in the tutorials: *How Indicators Work* (pandas) and *How Expressions Work* (polars).

## Choosing and mixing

Choose by your data, not by the charts: if your pipeline produces pandas frames, import from `mplchart.indicators`; if polars, from `mplchart.expressions`. The two systems don't cross — applying a pandas indicator to a polars frame (or a polars expression to a pandas frame) raises a `TypeError` rather than converting behind your back.

Plain callables are the one universal escape hatch: any function taking the prices frame and returning an aligned series plots directly on either backend, receiving the native frame type.

## Why two systems instead of one

Indicators predate the polars backend and lean on pandas idioms (`rolling`, `ewm`, `.pipe`). When polars support was added, wrapping polars in the same object model would have hidden its best feature: expressions are *composable, lazy, and native* — `SMA(20, src=(HIGH + LOW) / 2)` is just polars, usable in `select` and `with_columns` outside charting. Keeping the two systems separate keeps each idiomatic to its engine, with the chart layer as the common ground.
