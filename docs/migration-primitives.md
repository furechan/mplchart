# Primitives Migration Analysis

Status of each primitive in [src/mplchart/primitives/](../src/mplchart/primitives/) relative to the polars migration.

## Already migrated

| Primitive | File | Status |
|---|---|---|
| `Candlesticks` | [candlesticks.py](../src/mplchart/primitives/candlesticks.py) | Done — uses `col_to_numpy` + `mapper.rownum` |
| `Volume` | [volume.py](../src/mplchart/primitives/volume.py) | Done — uses `col_to_numpy` + `mapper.rownum` |
| `OHLC` | [ohlc.py](../src/mplchart/primitives/ohlc.py) | Done — uses `col_to_numpy` + `mapper.rownum` |
| `Price` | [price.py](../src/mplchart/primitives/price.py) | Done — uses `chart.plot_xy()` |
| `LinePlot` | [lineplot.py](../src/mplchart/primitives/lineplot.py) | Done — uses `chart.plot_xy()` |
| `AreaPlot` | [areaplot.py](../src/mplchart/primitives/areaplot.py) | Done — uses `chart.plot_xy()` |
| `BarPlot` | [barplot.py](../src/mplchart/primitives/barplot.py) | Done — uses `chart.plot_xy()` |

## Remaining — pandas-only

### Peaks ([peaks.py](../src/mplchart/primitives/peaks.py))

**Pandas dependencies:**
- `extract_peaks` builds `pd.Series(np.nan, prices.index)` and uses `rolling().max()`/`rolling().min()`
- `plot_handler` uses `data.index` as x-coordinates after `chart.slice(data)`

**Complication:** Returns a sparse series (`dropna()`), so x/y cannot be derived from the window slice alone — the sparse x-positions must come from the data itself.

**Migration path:** Replace `extract_peaks` with a pure-numpy implementation that returns `(row_indices, values)` directly. Use `chart.mapper.rownum[row_indices]` for x.

**Known bug:** `__ror__` doesn't return the cloned result — `self.clone(indicator=indicator)` result is discarded.

---

### ZigZag ([zigzag.py](../src/mplchart/primitives/zigzag.py))

**Pandas dependencies:**
- `calc_zigzag` uses `prices.itertuples()` to iterate rows
- Uses `prices.index[index]` to map integer positions to datetime index labels
- Result is a sparse Series; `chart.slice()` + `series_xy()` used for x/y

**Complication:** Also sparse — same issue as Peaks. The integer row indices are already computed internally in `calc_zigzag` (variable `index`), so migration is straightforward: instead of `prices.index[index]`, store the integer row indices and map through `chart.mapper.rownum`.

**Migration path:** Change `calc_zigzag` to accept a 2D numpy array (rows × columns) and return `(row_indices, values)`. `plot_handler` maps through `chart.mapper.rownum[row_indices]`.

---

### Stripes ([stripes.py](../src/mplchart/primitives/stripes.py))

**Pandas dependencies:**
- `result.eval(self.expr)` — pandas DataFrame eval
- `np.sign(result).ffill()` — pandas Series ffill
- `.diff().fillna(0).ne(0).cumsum()` — pandas diff/fillna/cumsum
- `flag[flag > 0].index.to_series().groupby(csum).agg(['first', 'last'])` — pandas groupby
- `ax.axvspan(x1, x2, ...)` where x1/x2 are index values (datetime or rownum)

**Complication:** The `axvspan` calls use x1/x2 from the sliced result's index. After migration, the index would already be rownums (from `DateIndexMapper.slice`), so the `axvspan` calls would work as-is. The main blocker is `eval()` and the pandas signal processing chain.

**Migration path:** Non-trivial. Requires rewriting the signal processing with numpy (replacing `ffill`, `diff`, `groupby`). The `eval` expression feature is inherently pandas.

---

### Markers ([markers.py](../src/mplchart/primitives/markers.py))

**Pandas dependencies:**
- `result.eval(self.expr)` — pandas DataFrame eval
- `prices.assign(flag=flag)` — pandas assign
- `.ffill().diff().fillna(0).ne(0)` — pandas chain
- Boolean indexing `result[mask]`
- `result.index` for x, `result.close` for y

**Complication:** Similar to Stripes. Also uses `prices.assign()` to attach the computed flag back to the prices DataFrame before slicing, which is a pandas pattern.

**Migration path:** Non-trivial for the same reasons as Stripes. The `eval` feature is pandas-only.

---

## Summary

| Primitive | Calculation | X-coords source | Migration difficulty |
|---|---|---|---|
| `Peaks` | `pd.rolling` | sparse index | Medium — pure numpy rolling possible |
| `ZigZag` | `itertuples`, sparse index | sparse index | Easy — row indices already computed |
| `Stripes` | `eval`, `ffill`, `diff`, `groupby` | slice index | Hard — `eval` is pandas-only |
| `Markers` | `eval`, `assign`, `ffill`, `diff` | slice index | Hard — `eval` is pandas-only |
