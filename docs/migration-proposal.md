# Pandas → Pandas + Polars Migration Proposal

## Goal

Accept polars DataFrames at the `Chart` API and support polars `Expr` objects as column
selectors / indicator arguments when the input data is polars-based.

---

## Architecture

### Data normalization

At Chart initialization, column names are lowercased for both backends. That's it.

- **pandas** — keep the DatetimeIndex as-is
- **polars** — already has a flat `"datetime"` column

`extract_datetime(df)` handles the difference: strips timezone and returns a tz-naive
numpy array in local (wall-clock) time so axis labels display correctly without the
formatter needing to know the timezone.

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

Takes the tz-naive datetime numpy array (extracted once at init) plus optional
constraints, returns a `slice(start_row, end_row)`. Uses `np.searchsorted` throughout —
one implementation, works for both backends.

### Pipeline per primitive

```
prices (pandas | polars)
    │
    ▼  1. COMPUTE
indicator.__call__(prices)  or  pl.Expr evaluated against prices
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
   Windowing is then a trivial slice with no join or reindex needed.

2. **Irregular primitives** (`zigzag`, `peaks`, `stripes`, `markers`) own their x/y
   extraction. They compute their own row indices and index into `rownum` to get x-positions.

---

## Refactoring list — easiest → most involved

### Phase 1 — Infrastructure (no behavior change)

**1.1** Move `polars` from dev-only → optional dependency in `pyproject.toml`

**1.2** Add backend detection helpers in `utils.py`:
- `is_polars(df)` / `is_pandas(df)` — duck-type via `type(df).__module__` prefix
- `detect_backend(df) -> str` — returns `"polars"` or `"pandas"`
- `is_expr(item) -> bool` — duck-type via `hasattr(item, "meta")`, no polars import

**1.3** Add `normalize_columns(df)` in `utils.py` — lowercases column names, branches on `detect_backend`

**1.4** Add `extract_datetime(df) -> np.ndarray` in `utils.py` — strips timezone and returns
tz-naive numpy array in local time; branches on `detect_backend`

**1.5** Add `col_to_numpy(df, col) -> np.ndarray` in `utils.py` — extracts a named column
as numpy array for both backends

**1.6** Add `is_expr` + update `series_data()` / `get_series()` in `utils.py` to accept
`pl.Expr` as `item` via `is_expr` duck-typing check

**1.7** Add baseline test `tests/test_polars.py` using `sample_prices(backend="polars")`
_(no fixes — just documents what breaks today)_

---

### Phase 2 — Chart: keep prices in native format

**2.1** Split `Chart.prepare()` into `prepare_pandas()` and `prepare_polars()`, dispatched
by `detect_backend()` — removes the eager `to_pandas()` conversion

**2.2** Store `self.backend = detect_backend(prices)` on the Chart

---

### Phase 3 — Mapper: `rownum` + `window` slice

**3.1** Replace pandas `DatetimeIndex` storage with numpy `datetime_array` from `extract_datetime()`

**3.2** Compute `rownum = np.arange(len(datetime_array))` at init

**3.3** Implement `calc_window(start, end, max_bars) -> slice` using `np.searchsorted`
— one pure-numpy implementation, no pandas/polars

**3.4** Implement `series_xy(values, window)` on the mapper — `rownum[window], values[window]`

**3.5** Remove all `pd.Series`, `.align()`, `.set_axis()`, `.loc[]`, `.slice_indexer()`
from `mapper.py`

**3.6** Update `config_axes()` to pass `datetime_array` directly to `DTArrayLocator` /
`DTArrayFormatter` instead of `self.index.tz_localize(None)`

---

### Phase 4 — Primitives: replace index/values access

**4.1** Replace `.index.values` / `.values` / `.iloc[n]` in `plotters.py` with
`col_to_numpy()` and `mapper.series_xy()`

**4.2** Replace attribute-style column access (`data.high`, `data.low`, etc.) in
`primitives/candlesticks.py`, `volume.py`, `ohlc.py`, `price.py` with `col_to_numpy()`

**4.3** Update `LinePlot` and `Peaks` `item=` parameter to accept `pl.Expr` (type widened,
threaded through to `series_data()`)

**4.4** Audit irregular primitives (`zigzag`, `peaks`, `stripes`, `markers`): replace
datetime/index-based x coordinates with `rownum[row_indices]`

---

### Phase 5 — Expression support in the plot API

**5.1** Add `PolarsExprIndicator` in `model.py`: wraps a `pl.Expr` or tuple of `pl.Expr`,
evaluates via `prices.select(expr)`, returns same-length polars Series (or tuple of Series)

**5.2** In `Chart.plot()`: detect `pl.Expr` / tuple-of-`pl.Expr` via `is_expr()` and
auto-wrap in `PolarsExprIndicator` — no polars import in `chart.py`

---

### Phase 6 — `expressions/` subpackage

**6.1** Create `src/mplchart/expressions/` with the same conventions as bearta:
- `prelude.py`: `wrap_expression` decorator, `OPEN`, `HIGH`, `LOW`, `CLOSE`, `VOLUME` constants
- `trend.py`: `SMA`, `EMA`, `WMA`, `HMA`, `DEMA`, `TEMA`
- `momentum.py`: `ROC`, `MOM`, `RSI`, `MACD`, `STOCH`
- `volatility.py`: `TRANGE`, `ATR`, `BBANDS`, `DONCHIAN`, `KELTNER`
- `prices.py`: `MIDPRICE`, `TYPPRICE`, `WCLPRICE`

**6.2** Multi-column expressions return a tuple of `pl.Expr` (not `pl.struct`) — each
evaluated independently, `series_xy` called once per element

---

### Phase 7 — End-to-end test coverage

**7.1** Verify all existing `Indicator.__call__` implementations still work with pandas
after the mapper/primitive refactor

**7.2** Expand `tests/test_polars.py` to cover expressions from the `expressions/`
subpackage with polars input

---

## Dependency map

```
Phase 1 (utils helpers)
    └─ Phase 2 (Chart: native format)
           └─ Phase 3 (mapper: rownum + window slice)
                  └─ Phase 4 (primitives: col_to_numpy + series_xy)
                         ├─ Phase 5 (Expr in plot API)
                         ├─ Phase 6 (expressions/ subpackage)
                         └─ Phase 7 (end-to-end tests)
```

Phases 1–4 are the load-bearing refactor. Once the mapper and primitives are backend-agnostic,
Phases 5–7 are incremental additions with low risk.
