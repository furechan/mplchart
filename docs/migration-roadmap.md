# Pandas → Pandas + Polars Migration Plan

## Goal

Accept polars DataFrames at the `Chart` API and support polars `Expr` objects as column
selectors / indicator arguments when the input data is polars-based.

---

## Architecture

### Data normalization

At Chart initialization, column names are lowercased for both backends. That's it.

- **pandas** — keep the DatetimeIndex as-is
- **polars** — already has a flat `"datetime"` column

`extract_datetime(df)` handles the difference: extracts from `df.index` for pandas,
from `df["datetime"]` for polars. Everything downstream is pure numpy.

### The mapper collapses to `rownum` + window slice

`rownum` is literally the row index: row 0, 1, 2, … Friday is row N, Monday is row N+1.
Using row numbers as matplotlib x-coordinates is precisely what removes weekend/holiday gaps —
no special gap-removal logic needed.

At `Chart` init, `rownum` is just `np.arange(len(prices))`. The mapper becomes just two things:

- **`rownum`**: 1-D integer numpy array `[0, 1, 2, …]`, computed once at init
- **`window`**: a `slice(start_row, end_row)` selecting the visible bar range

`array[window]` works uniformly on numpy arrays, pandas Series, and polars Series.
There is no index alignment, no `pd.Series`, no `.align()`, no `.loc[]`.

### `calc_window`

```python
def calc_window(datetime_array, *, start=None, end=None, max_bars=None) -> slice:
```

Takes the datetime numpy array (extracted from prices once at init) plus optional
constraints, returns a `slice(start_row, end_row)`. Uses `np.searchsorted` throughout —
one implementation, works for both backends.

### Pipeline per primitive

```
prices (pandas | polars, flat datetime column)
    │
    ▼  1. COMPUTE
indicator.__call__(prices)  or  pl.Expr.evaluate(prices)
    → same-length result (NaN where undefined)
    │
    ▼  2. SLICE
window = slice(start_row, end_row)
rownum[window], values[window]
    │
    ▼  3. series_xy(rownum[window], values[window]) → (x: np.ndarray, y: np.ndarray)
    │
    ▼  4. PLOT
matplotlib receives plain numpy arrays
```

### `series_xy`

```python
def series_xy(rownum, values, window):
    return rownum[window], values[window]
```

Multi-column results: call once per column, same `rownum`, same `window`.

### Key constraints

1. **Indicators return same-length output** — positionally aligned with input prices.
   Windowing is then a trivial mask with no join or reindex needed.

2. **Irregular primitives** (`zigzag`, `peaks`, `stripes`, `markers`) own their x/y
   extraction. They compute their own row indices and index into `rownum` to get x-positions.
   Same `rownum`, different selection logic.

---

## Refactoring list — easiest → most involved

### Phase 1 — Infrastructure (no behavior change)

**1.1** Move `polars` from dev-only → optional dependency in `pyproject.toml`

**1.2** Add `is_polars(df)` / `is_pandas(df)` helpers in `utils.py`
_(duck-type via `__module__` prefix — same pattern as existing `convert_dataframe`)_

**1.3** Add `normalize_columns(df)` in `utils.py` — lowercases column names for both backends

**1.4** Add baseline test `tests/test_polars.py` using `sample_prices(backend="polars")`
_(no fixes — just documents what breaks today)_

---

### Phase 2 — Normalize prices to flat datetime column

**2.1** Update `Chart.prepare()`:
- lowercase columns (`normalize_columns`) for both backends
- pandas: keep DatetimeIndex as-is
- polars: no conversion, no `to_pandas()`

**2.2** Remove `to_pandas()` call from `Chart.prepare()` — keep prices in native format

**2.3** Store `self.backend: str` (`"pandas"` or `"polars"`) on the Chart

---

### Phase 3 — Mapper: `rownum` + `window` slice

**3.1** At `Chart.init_mapper()`, call `extract_datetime(prices)` to get the datetime numpy array:
`df.index.values` for pandas, `df["datetime"].to_numpy()` for polars — store as `self.datetime_array`

**3.2** Compute `self.rownum = np.arange(len(prices))`

**3.3** Implement `calc_window(datetime_array, *, start, end, max_bars) -> slice` using
`np.searchsorted` — one pure-numpy implementation, no pandas/polars

**3.4** Remove all `pd.Series`, `.align()`, `.set_axis()`, `.loc[]`, `.slice_indexer()`
from `mapper.py`

**3.5** Handle timezone operations without pandas
_(replace `.tz_localize()` / `.tz_convert()` with `zoneinfo` / `datetime.timezone`)_

---

### Phase 4 — `series_xy` and column extraction helpers

**4.1** Rewrite `series_xy(rownum, values, window)` in `utils.py` — pure numpy, no pandas/polars

**4.2** Add `col_to_numpy(df, col)` helper — extracts a named column as numpy array for
both backends _(pandas: `df[col].to_numpy()` | polars: `df[col].to_numpy()`)_

---

### Phase 5 — Primitives: replace index/values access with `col_to_numpy` + `series_xy`

**5.1** Replace `.index.values` in `plotters.py` with `rownum[window]`

**5.2** Replace `.values` (Series → numpy) in `plotters.py` with `col_to_numpy()`

**5.3** Replace `.iloc[n]` in `plotters.py` with row-position access

**5.4** Replace attribute-style column access in `primitives/candlesticks.py`
(`data.high`, `data.low`) with `col_to_numpy(data, "high")` etc.

**5.5** Same in `primitives/volume.py`, `ohlc.py`, `price.py`

**5.6** Audit irregular primitives (`zigzag`, `peaks`, `stripes`, `markers`): ensure they
use `rownum[their_row_indices]` for x — document that they own their coordinate extraction

---

### Phase 6 — Expression support in the plot API

**6.1** Create `PolarsExprIndicator` in `model.py`: wraps a `pl.Expr`, evaluates via
`prices.select(expr)`, returns a same-length polars Series or struct

**6.2** Modify `Chart.plot()` to detect `polars.Expr` objects and auto-wrap in
`PolarsExprIndicator`

**6.3** Wire `calc_result()` in `chart.py` for `PolarsExprIndicator` — result is a
same-length Series or struct, fed into `col_to_numpy()` + `series_xy()` like any other

**6.4** Handle tuple-of-Expr results: evaluate each expression independently and call
`series_xy` once per element — same as iterating over columns of a multi-column DataFrame

---

### Phase 7 — `expressions/` subpackage

**7.1** Create `src/mplchart/expressions/` subpackage with the same conventions as bearta:
- `wrap_expression` decorator enabling `SMA(20, pl.col("close"))` or `SMA(20)` (defaults to `CLOSE`)
- Prelude constants: `OPEN`, `HIGH`, `LOW`, `CLOSE`, `VOLUME`
- Factory functions returning `pl.Expr`: `SMA`, `EMA`, `WMA`, `HMA`, `DEMA`, `TEMA`
- Momentum: `ROC`, `MOM`, `RSI`, `MACD`, `STOCH`
- Volatility: `ATR`, `TRANGE`, `BBANDS`, `DONCHIAN`, `KELTNER`
- Prices: `MIDPRICE`, `TYPPRICE`, `WCLPRICE`

**7.2** Multi-column expressions (MACD, BBANDS, etc.) return a tuple of `pl.Expr`, one per
output series — each evaluated independently, `series_xy` called once per element

**7.3** Add `item=` support for `polars.Expr` in `LinePlot` and `Peaks` — thread through
to `series_data()`

---

### Phase 8 — End-to-end polars path + test coverage

**8.1** Verify all `Indicator.__call__` implementations still work correctly with pandas
after the mapper/primitive refactor

**8.2** Expand `tests/test_polars.py` to cover expressions from the `expressions/`
subpackage with polars input

---

## Dependency map

```
Phase 1 (infra)
    └─ Phase 2 (normalize to flat datetime column)
           └─ Phase 3 (mapper: rownum + mask, no DatetimeIndex)
                  └─ Phase 4 (series_xy + col_to_numpy helpers)
                         └─ Phase 5 (primitives use helpers)
                                ├─ Phase 6 (Expr in plot API)   ← early value
                                ├─ Phase 7 (item= Expr)
                                └─ Phase 8 (end-to-end test coverage)
```

Phases 2–5 are the load-bearing refactor. Once prices are flat and `series_xy` works
for both backends, Phases 6–10 are incremental with low risk.
