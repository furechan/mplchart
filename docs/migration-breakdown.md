# Migration Breakdown — per file

---

## [pyproject.toml](../pyproject.toml)

**Move `polars` from dev → optional dependency**

```toml
# before
[tool.uv.dev-dependencies]
polars = "*"

# after
[project.optional-dependencies]
polars = ["polars"]
```

---

## [src/mplchart/utils.py](../src/mplchart/utils.py)

**Add `is_polars` / `is_pandas` / `detect_backend` helpers**

Backend detection by module prefix, consistent with the existing `convert_dataframe` pattern.

```python
def is_polars(df) -> bool:
    return getattr(type(df), "__module__", "").startswith("polars")

def is_pandas(df) -> bool:
    return getattr(type(df), "__module__", "").startswith("pandas")

def detect_backend(df) -> str:
    return getattr(type(df), "__module__", "").partition(".")[0]
```

---

**Add `normalize_columns(df)`**

Lowercases all column names for both backends. Replaces the inline
`prices.rename(columns=str.lower, inplace=True)` in `Chart.prepare()`.

```python
def normalize_columns(df):
    match detect_backend(df):
        case "polars":
            return df.rename({c: c.lower() for c in df.columns})
        case "pandas":
            return df.rename(columns=str.lower)
        case backend:
            raise ValueError(f"Unsupported backend {backend!r}")
```

---

**Add `col_to_numpy(df, col) -> np.ndarray`**

Extracts a named column as a 1-D numpy array from either backend.
Used by primitives and the mapper. The API is the same for both
(`df[col].to_numpy()`) but the type of `df[col]` differs.

```python
def col_to_numpy(df, col: str) -> np.ndarray:
    return df[col].to_numpy()
```

---

**Add `is_expr(item)` helper**

No polars import — `pl.Expr` exposes a `.meta` attribute that plain strings do not.

```python
def is_expr(item) -> bool:
    return hasattr(item, "meta")
```

**Update `series_data()` / `get_series()` to accept `pl.Expr` as `item`**

```python
# before
def series_data(data, item: str | None = None, *, default_item: str | None = None):
    if hasattr(data, "columns"):
        if item is not None:
            return data[item]
        ...

# after
def series_data(data, item=None, *, default_item: str | None = None):
    if is_expr(item):
        return data.select(item).to_series()
    if hasattr(data, "columns"):
        if item is not None:
            return data[item]
        ...
```

---

## [src/mplchart/chart.py](../src/mplchart/chart.py)

**Split `prepare()` into `prepare_pandas()` and `prepare_polars()`, branch on `detect_backend()`**

Currently `prepare()` converts everything to pandas eagerly. Replace with two
backend-specific implementations and a dispatcher.

```python
@staticmethod
def prepare_pandas(prices):
    prices = prices.rename(columns=str.lower)
    if "datetime" in prices.columns:
        prices = prices.set_index("datetime")
    elif "date" in prices.columns:
        prices = prices.set_index("date")
    else:
        prices = prices.rename_axis(index=str.lower)
    return prices

@staticmethod
def prepare_polars(prices):
    return normalize_columns(prices)   # lowercase only, keep flat datetime column

@staticmethod
def prepare(prices):
    if detect_backend(prices) == "polars":
        return Chart.prepare_polars(prices)
    return Chart.prepare_pandas(prices)
```

---

**Store `self.backend`**

```python
self.backend = detect_backend(prices)   # "polars" or "pandas"
```

---

**Extract datetime array in `init_mapper()` via `extract_datetime()`**

```python
def init_mapper(self, prices):
    datetime_array = extract_datetime(prices)
    self.mapper = DateIndexMapper(datetime_array, max_bars=self.max_bars,
                                  start=self.start, end=self.end)
```

Where `extract_datetime` lives in `utils.py`:

```python
def extract_datetime(df) -> np.ndarray:
    match detect_backend(df):
        case "polars":
            return df["datetime"].dt.replace_time_zone(None).to_numpy()
        case "pandas":
            return df.index.tz_localize(None).values
        case backend:
            raise ValueError(f"Unsupported backend {backend!r}")
```

---

**Detect `pl.Expr` in `plot()` and wrap in `PolarsExprIndicator`**

```python
# in plot() / plot_indicator(), before dispatching:
if is_expr(indicator):
    indicator = PolarsExprIndicator(indicator)
elif isinstance(indicator, tuple) and all(is_expr(e) for e in indicator):
    indicator = PolarsExprIndicator(indicator)   # tuple of Expr
```

---

## [src/mplchart/model.py](../src/mplchart/model.py)

**Add `PolarsExprIndicator`**

Wraps a single `pl.Expr` or a tuple of `pl.Expr`. When called with `prices`,
evaluates each expression against the polars DataFrame and returns same-length
Series (single) or a tuple of Series (multi).

```python
class PolarsExprIndicator(Indicator):
    def __init__(self, expr):
        # expr is pl.Expr or tuple[pl.Expr, ...]
        self.expr = expr

    def __call__(self, prices):
        if isinstance(self.expr, tuple):
            return tuple(prices.select(e).to_series() for e in self.expr)
        return prices.select(self.expr).to_series()
```

---

## [src/mplchart/mapper.py](../src/mplchart/mapper.py)

**Replace pandas `DatetimeIndex` with numpy `datetime_array` + `rownum`**

`DateIndexMapper` currently stores `self.index` (a pandas `DatetimeIndex`) and
builds `xloc` by creating a `pd.Series` with that index on every `.slice()` call.

```python
# before
class DateIndexMapper:
    def __init__(self, index, *, max_bars=None, start=None, end=None):
        if start or end:
            locs = index.tz_localize(None).slice_indexer(start=start, end=end)
            index = index[locs]
        if max_bars and max_bars > 0:
            index = index[-max_bars:]
        self.index = index                   # pandas DatetimeIndex

    def slice(self, data):
        xloc = pd.Series(np.arange(len(self.index)), index=self.index, name="xloc")
        xloc, data = xloc.align(data, join="inner")
        data = data.set_axis(xloc)
        return data
```

After the refactor, the mapper stores a numpy `datetime_array` and `rownum`, and
exposes a `calc_window()` + `series_xy()` API. No pandas anywhere.

```python
# after
class DateIndexMapper:
    def __init__(self, datetime_array: np.ndarray, *, max_bars=None, start=None, end=None):
        # apply start/end via searchsorted
        lo = np.searchsorted(datetime_array, np.datetime64(start)) if start else 0
        hi = np.searchsorted(datetime_array, np.datetime64(end), side="right") if end else len(datetime_array)
        datetime_array = datetime_array[lo:hi]

        if max_bars and max_bars > 0:
            datetime_array = datetime_array[-max_bars:]

        self.datetime_array = datetime_array
        self.rownum = np.arange(len(datetime_array))

    def calc_window(self, start=None, end=None, max_bars=None) -> slice:
        """Return a slice(start_row, end_row) for the visible bar range."""
        lo = np.searchsorted(self.datetime_array, np.datetime64(start)) if start else 0
        hi = np.searchsorted(self.datetime_array, np.datetime64(end), side="right") if end else len(self.datetime_array)
        if max_bars and max_bars > 0:
            lo = max(lo, hi - max_bars)
        return slice(lo, hi)

    def series_xy(self, values, window: slice) -> tuple[np.ndarray, np.ndarray]:
        """Return (x, y) numpy arrays for the given window."""
        return self.rownum[window], np.asarray(values)[window]

    def map_date(self, date) -> int:
        """Map a single date to its rownum (for plot_vline)."""
        return int(np.searchsorted(self.datetime_array, np.datetime64(date), side="left"))
```

**Replace `.tz_localize()` / `.tz_convert()` with `zoneinfo`**

```python
# before
locs = index.tz_localize(None).slice_indexer(start=start, end=end)

# after — strip tz from numpy datetime64 before searchsorted
# numpy datetime64 arrays are already tz-naive; no pandas needed
lo = np.searchsorted(datetime_array, np.datetime64(start))
```

**Update `config_axes()`** — `DTArrayLocator` / `DTArrayFormatter` currently receive
`self.index.tz_localize(None)`. Pass `self.datetime_array` directly instead.

```python
def config_axes(self, ax):
    locator = DTArrayLocator(self.datetime_array)
    formatter = DTArrayFormatter(self.datetime_array)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
```

---

## [src/mplchart/plotters.py](../src/mplchart/plotters.py)

**Replace `series_xy` — currently uses `.index.values` and `.values`**

`AutoPlotter.series_xy()` at line 49–58 extracts x/y by reading the pandas index and
`.values`. After the mapper refactor, it delegates to `mapper.series_xy()` instead.

```python
# before
def series_xy(self, item=None):
    if self.data.__class__.__name__ == "Series":
        series = self.data
    elif item is not None:
        series = self.data[item]
    else:
        series = self.data.iloc[:, 0]
    return series.index.values, series.values   # ← pandas-specific

# after
def series_xy(self, item=None):
    if item is not None:
        values = col_to_numpy(self.data, item)
    elif hasattr(self.data, "columns"):
        values = col_to_numpy(self.data, self.data.columns[0])
    else:
        values = np.asarray(self.data)
    return self.chart.mapper.series_xy(values, self.window)
```

`self.window` is the `slice` computed once per `plot_indicator()` call and stored on
the plotter.

**Replace `get_columns()` — currently uses `hasattr(data, "columns")`**

Works for both backends already since polars also has `.columns`. No change needed,
but worth verifying polars `DataFrame.columns` returns a list of strings (it does).

---

## [src/mplchart/primitives/candlesticks.py](../src/mplchart/primitives/candlesticks.py)

**Replace attribute-style column access and `.index.values`**

`plot_cspoly` and `plot_csbars` both access `data.high`, `data.low`, `data.open`,
`data.close` as pandas attributes, and read `data.index.values` for x-coordinates.

```python
# before (lines 91–99)
xvalues = data.index.values
high, low = data.high, data.low
change = data.close.pct_change()
bottom = np.minimum(data.open, data.close)
top = np.maximum(data.open, data.close)

# after
xvalues = mapper.rownum[window]            # integer row numbers, no dates
high    = col_to_numpy(data, "high")
low     = col_to_numpy(data, "low")
open_   = col_to_numpy(data, "open")
close   = col_to_numpy(data, "close")
change  = np.diff(close, prepend=np.nan) / close  # pct_change without pandas
bottom  = np.minimum(open_, close)
top     = np.maximum(open_, close)
```

`chart.slice(prices)` becomes `prices[window]` (a DataFrame slice), and the mapper
provides `rownum[window]` for the x-axis.

---

## [src/mplchart/primitives/volume.py](../src/mplchart/primitives/volume.py)

**Replace `prices.volume`, `prices.close.pct_change()`, `pd.DataFrame`, and `.index`**

`Volume.process()` at line 51–62 builds a pandas DataFrame using attribute access and
`.rolling()`. The `plot_handler` then reads `data.index` for the x-axis.

```python
# before
def process(self, prices):
    volume = prices.volume
    change = prices.close.pct_change()
    result = dict(volume=volume, change=change)
    if self.sma:
        result["average"] = volume.rolling(self.sma).mean()
    return pd.DataFrame(result)

# after — work with native format
def process(self, prices):
    volume = col_to_numpy(prices, "volume")
    close  = col_to_numpy(prices, "close")
    change = np.diff(close, prepend=np.nan) / close
    result = dict(volume=volume, change=change)
    if self.sma:
        # simple rolling mean on numpy
        result["average"] = np.convolve(volume, np.ones(self.sma)/self.sma, mode="same")
    return result   # plain dict of numpy arrays, no DataFrame needed
```

```python
# before (plot_handler)
index = data.index
ax.bar(index, volume, ...)

# after
xvalues = mapper.rownum[window]
ax.bar(xvalues, volume[window], ...)
```

---

## [src/mplchart/primitives/lineplot.py](../src/mplchart/primitives/lineplot.py)

**Update `item` type annotation to accept `pl.Expr`**

`item` is currently `str | None`. After the change it is `str | pl.Expr | None`.
`series_data()` already handles `pl.Expr` once updated in `utils.py`, so the
primitive just needs to widen the type and pass it through unchanged.

```python
# before
def __init__(self, item: str | None = None, ...):

# after
def __init__(self, item: str | pl.Expr | None = None, ...):
```

**Replace `series_xy(series)` call with mapper-based extraction**

```python
# before
xv, yv = series_xy(series)
ax.plot(xv, yv, ...)

# after
yv = col_to_numpy(series, ...)   # or np.asarray(series)
xv = chart.mapper.rownum[window]
ax.plot(xv, yv, ...)
```

---

## [src/mplchart/primitives/peaks.py](../src/mplchart/primitives/peaks.py)

**Irregular primitive — owns its own x/y extraction**

`extract_peaks()` currently returns a sparse pandas Series (`.dropna()` removes
non-peak rows, making it shorter than the input). It uses `prices.index` and
`pd.Series(np.nan, prices.index)` internally.

This primitive cannot use the standard `series_xy` path because its output is not
same-length. It uses `rownum[peak_row_indices]` for x instead.

```python
# before
def extract_peaks(prices, span=1):
    peaks = pd.Series(np.nan, prices.index)
    mask = high.rolling(window, center=True).max() == high
    peaks.mask(mask, high, inplace=True)
    ...
    return peaks.dropna()   # sparse — length < len(prices)

# plot_handler:
xv, yv = data.index, data   # pandas index as x
ax.scatter(xv, yv, ...)

# after — track row positions explicitly
def extract_peaks(prices, span=1, rownum=None):
    # work on numpy arrays
    high = col_to_numpy(prices, "high")
    low  = col_to_numpy(prices, "low")
    # ... compute peak mask ...
    peak_rows = np.where(peak_mask)[0]
    peak_vals = high[peak_rows]   # or low
    peak_x    = rownum[peak_rows] if rownum is not None else peak_rows
    return peak_x, peak_vals

# plot_handler:
xv, yv = extract_peaks(data, span=self.span, rownum=chart.mapper.rownum)
ax.scatter(xv, yv, ...)
```

**Update `item` type to accept `pl.Expr`** (same as `LinePlot` above)

---

## [src/mplchart/primitives/zigzag.py](../src/mplchart/primitives/zigzag.py)

**Irregular primitive — already tracks row indices, needs `rownum` for x**

`calc_zigzag()` at line 8–65 iterates rows and collects pivot indices into a list,
then does `prices.index[index]` at line 63 to convert to datetime labels for the
x-axis. After the refactor, use `rownum[index]` (integer positions) instead.

```python
# before (line 63–65)
index = prices.index[index]
return pd.Series(values, index)

# after — return x as rownum, y as numpy
return rownum[index], np.array(values)
```

```python
# plot_handler before
xv, yv = series_xy(series)   # series has datetime index → x is dates

# plot_handler after
xv, yv = calc_zigzag(prices, threshold=self.threshold,
                     rownum=chart.mapper.rownum[window])
ax.plot(xv, yv, ...)
```

---

## [src/mplchart/primitives/stripes.py](../src/mplchart/primitives/stripes.py)

**Heavily pandas-specific — uses `.eval()`, `.ffill()`, `.diff()`, `.groupby()`, `.axvspan()`**

`Stripes` applies a pandas `eval` expression to the indicator result, then groups
consecutive `True` spans and draws `ax.axvspan(x1, x2)` using datetime values as x.

This primitive needs the most rework among irregular primitives:

```python
# before (lines 52–63)
if self.expr:
    result = result.eval(self.expr)           # pandas eval
flag = np.clip(np.sign(result), 0.0, 1.0).ffill()
csum = flag.diff().fillna(0).ne(0).cumsum()
aggs = flag[flag > 0].index.to_series().groupby(csum).agg(['first', 'last'])
for x1, x2 in aggs.itertuples(index=False, name=None):
    ax.axvspan(x1, x2, ...)                  # x1, x2 are datetimes

# after — expr becomes a pl.Expr or str, x coordinates are rownum
flag = np.clip(np.sign(signal), 0.0, 1.0)
# find contiguous True runs on numpy
edges = np.diff(flag, prepend=0, append=0)
starts = np.where(edges == 1)[0]
ends   = np.where(edges == -1)[0] - 1
for s, e in zip(starts, ends):
    ax.axvspan(rownum[s], rownum[e], ...)    # integer x coordinates
```

The `expr` parameter changes from a pandas eval string to a `pl.Expr` (polars) or
remains a string for pandas (needs dispatch based on backend).

---

## [src/mplchart/primitives/markers.py](../src/mplchart/primitives/markers.py)

**Uses `.eval()`, `.ffill()`, `.diff()`, `.index`, `.close` attribute access**

`Markers.plot_handler()` at line 52–85 applies a pandas `eval` expression, uses
`prices.assign(flag=flag)`, then reads `result.index` and `result.close` for scatter
coordinates.

```python
# before (lines 67–75)
mask = result.flag.ffill().diff().fillna(0).ne(0)
result = result[mask]
xv = result.index        # datetime x
yv = result.close        # attribute access

# after
# flag is a numpy array; find transition rows
ffilled = pd.Series(flag).ffill().to_numpy()   # or implement ffill on numpy
transitions = np.where(np.diff(ffilled, prepend=np.nan) != 0)[0]
xv = chart.mapper.rownum[transitions]
yv = col_to_numpy(prices, "close")[transitions]
ax.scatter(xv, yv, ...)
```

The `expr` parameter has the same issue as `Stripes` — currently a pandas eval string,
needs to become a `pl.Expr` or be dispatched by backend.

---

## [src/mplchart/expressions/](../src/mplchart/expressions/) (new subpackage)

**`expressions/prelude.py`**

Same `wrap_expression` decorator pattern as bearta. Enables both
`SMA(20, pl.col("close"))` (positional expr) and `SMA(20)` (defaults to `CLOSE`).

```python
import polars as pl
from functools import wraps

OPEN   = pl.col("open")
HIGH   = pl.col("high")
LOW    = pl.col("low")
CLOSE  = pl.col("close")
VOLUME = pl.col("volume")

def wrap_expression(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if args and isinstance(args[0], pl.Expr):
            kwargs["src"] = args[0]
            args = args[1:]
        return func(*args, **kwargs)
    return wrapper
```

**`expressions/trend.py`**

```python
@wrap_expression
def SMA(period: int, *, src: pl.Expr = CLOSE) -> pl.Expr:
    return src.rolling_mean(period, min_samples=period)

@wrap_expression
def EMA(period: int, *, src: pl.Expr = CLOSE) -> pl.Expr:
    return src.ewm_mean(span=period, min_samples=period)
```

**`expressions/momentum.py`**

```python
@wrap_expression
def RSI(period: int = 14, *, src: pl.Expr = CLOSE) -> pl.Expr:
    diff = src.diff()
    gain = diff.clip(0, None).ewm_mean(alpha=1/period)
    loss = (-diff).clip(0, None).ewm_mean(alpha=1/period)
    return 100 - (100 / (1 + gain / loss))

@wrap_expression
def MACD(n1=12, n2=26, n3=9, *, src: pl.Expr = CLOSE) -> tuple[pl.Expr, pl.Expr, pl.Expr]:
    macd   = EMA(n1, src=src) - EMA(n2, src=src)
    signal = EMA(n3, src=macd)
    hist   = macd - signal
    return macd, signal, hist   # tuple of Expr, not struct
```

**`expressions/volatility.py`**

```python
@wrap_expression
def ATR(period: int = 14, *, high=HIGH, low=LOW, close=CLOSE) -> pl.Expr:
    tr = pl.max_horizontal(high, close.shift(1)) - pl.min_horizontal(low, close.shift(1))
    return tr.ewm_mean(span=2 * period - 1)

@wrap_expression
def BBANDS(period=20, mult=2.0, *, src=CLOSE) -> tuple[pl.Expr, pl.Expr, pl.Expr]:
    mid   = src.rolling_mean(period)
    std   = src.rolling_std(period)
    return mid + mult * std, mid, mid - mult * std   # upper, middle, lower
```

**`expressions/__init__.py`**

Re-exports all public factories so users can do `from mplchart.expressions import SMA, EMA`.

---

## [tests/test_polars.py](../tests/test_polars.py) (new)

**Baseline test — documents what breaks before fixes**

```python
import pytest
polars = pytest.importorskip("polars")

from mplchart.samples import sample_prices
from mplchart.chart import Chart
from mplchart.primitives import Candlesticks

def test_polars_chart_init():
    prices = sample_prices("daily", backend="polars")
    chart = Chart(prices, max_bars=50)          # should not raise
    assert chart.backend == "polars"

def test_polars_expr():
    prices = sample_prices("daily", backend="polars")
    chart = Chart(prices, max_bars=50)
    chart.plot(Candlesticks(), polars.col("close").rolling_mean(20))
```
