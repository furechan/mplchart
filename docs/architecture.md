# Architecture

## Module layout

| Module | Role |
|---|---|
| `chart.py` | `Chart` — main entry point; owns the figure, mapper, and plotting pipeline |
| `model.py` | Base classes: `Primitive`, `Indicator`, `Wrapper`, `IndicatorChain` |
| `mapper.py` | `DateIndexMapper` (integer rownum x-axis) and `RawDateMapper` (datetime x-axis) |
| `primitives/` | Drawing primitives — operate directly on the prices DataFrame |
| `indicators.py` | Pandas-only indicator classes (subclass `Indicator`) |
| `library.py` | Pandas-only calc functions called by indicators |
| `expressions/` | Polars-only expression factories returning `pl.Expr` |
| `utils.py` | Backend detection, `apply_indicator`, `col_to_numpy`, `normalize_prices`, etc. |
| `layout.py` | Matplotlib figure/axes layout helpers |

## Backends

The core (`chart.py`, `mapper.py`, `primitives/`) is backend-agnostic. Backend-specific code is opt-in:
- `indicators.py` + `library.py` — pandas only; imported lazily
- `expressions/` — polars only; imported lazily

## Plotting pipeline

For each item passed to `chart.plot()`:
1. If it has `plot_handler` (a `Primitive`) → call it directly on unsliced prices
2. Otherwise compute: call `apply_indicator(prices, item)` → full-length result
3. Slice: `chart.slice(result)` → restricts to the visible window via the mapper
4. Select/create axes
5. If result is a `Wrapper` → call `wrapper.plot_result(data, chart, ax)`
6. Otherwise hand to `AutoPlot` for default line rendering

## Mapper

`DateIndexMapper` stores the full datetime array and uses **integer rownums** as matplotlib x-coordinates. This eliminates weekend/holiday gaps without any special logic. `DTArrayLocator` / `DTArrayFormatter` map tick positions back to date labels. `RawDateMapper` is an alternative that uses actual datetimes (matplotlib handles axis formatting).

## Operator conventions

| Operator | Context | Meaning |
|---|---|---|
| `SMA(50) \| LinePlot(...)` | pandas indicator → primitive | bind indicator to a rendering primitive |
| `SMA(50) \| EMA(10)` | indicator → indicator | chain: apply left then right |
| `RSI() @ LinePlot(...)` | polars expression → primitive | bind expression to a primitive |
| `prices \| SMA(50)` | data → indicator | apply indicator to data directly |

## Primitives

Regular primitives (`LinePlot`, `AreaPlot`, `BarPlot`, `AutoPlot`, `Price`) use `chart.mapper.series_xy(data)` for x/y extraction. Irregular primitives (`ZigZag`, `Peaks`, `Stripes`, `Markers`) compute their own sparse row indices and index into `mapper.rownum` directly.
