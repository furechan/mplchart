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
`prices.select(expr)`, returns a same-length polars Series

**6.2** Modify `Chart.plot()` to detect `polars.Expr` objects and auto-wrap in
`PolarsExprIndicator`

**6.3** Wire `calc_result()` in `chart.py` for `PolarsExprIndicator` — result is a
same-length Series, fed into `col_to_numpy()` + `series_xy()` like any other

---

### Phase 7 — `item=` parameter accepts polars Expr

**7.1** Extend `series_data()` / `get_series()` to accept `polars.Expr` as `item`
_(evaluate `df.select(item)` and return the first column)_

**7.2** Update `LinePlot` and `Peaks` to accept `polars.Expr` for `item=` and thread
it through to `series_data()`

---

### Phase 8 — Library functions: polars dispatch (single-series)

**8.1** Create `library_polars.py` with polars implementations of single-series rolling
functions: `calc_sma`, `calc_ema`, `calc_wma`, `calc_roc`, `calc_mom`, `calc_std`,
`calc_slope`, `calc_curve`

**8.2** Add `dispatch(fn_pandas, fn_polars)` wrapper in `library.py` routing on input type

**8.3** Wire dispatch for all single-series functions

---

### Phase 9 — Library functions: polars dispatch (multi-column)

**9.1** Polars implementations of multi-column functions: `calc_macd`, `calc_bbands`,
`calc_donchian`, `calc_keltner`

**9.2** Polars implementations of OHLCV functions: `calc_atr`, `calc_cci`, `calc_bop`,
`calc_adx`, `calc_dmi`

**9.3** Wire dispatch for all multi-column and OHLCV functions

---

### Phase 10 — End-to-end polars path + test coverage

**10.1** Verify all `Indicator.__call__` implementations flow through correctly once
library dispatch is wired — most need no changes

**10.2** Fix any indicator that hard-codes pandas operations (`pd.concat`, `pd.Series(...)`,
explicit `.index` access)

**10.3** Expand `tests/test_polars.py` to cover all indicators with polars input

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
                                └─ Phases 8–10 (library dispatch)
```

Phases 2–5 are the load-bearing refactor. Once prices are flat and `series_xy` works
for both backends, Phases 6–10 are incremental with low risk.
