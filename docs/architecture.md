# Architecture

Design notes: [axes-stickiness.md](axes-stickiness.md) — pane vs axes vocabulary and current-pane semantics.

## Module layout

| Module | Role |
|---|---|
| `chart.py` | `Chart` — main entry point; owns the figure, mapper, and plotting pipeline |
| `model/primitive.py` | `Primitive` and `BindingPrimitive` — backend-agnostic base classes |
| `model/indicator.py` | `Indicator` and `IndicatorChain` — pandas-only base classes |
| `mapper.py` | `DateIndexMapper` (integer rownum x-axis) and `RawDateMapper` (datetime x-axis) |
| `primitives/` | Drawing primitives — operate directly on the prices DataFrame |
| `indicators.py` | Pandas-only indicator classes (subclass `Indicator`) |
| `library.py` | Pandas-only calc functions called by indicators |
| `expressions/` | Polars-only expression factories returning `pl.Expr` (multi-output expressions return a `pl.struct(...)` Expr) |
| `utils.py` | Backend detection, `apply_indicator`, `col_to_numpy`, `normalize_prices`, etc. |
| `layout.py` | Matplotlib figure/axes layout helpers |

## Backends

The core (`chart.py`, `mapper.py`, `primitives/`) is backend-agnostic. Backend-specific code is opt-in:
- `indicators.py` + `library.py` — pandas only; imported lazily
- `expressions/` — polars only; imported lazily

## Plotting pipeline

For each item passed to `chart.plot()`:
1. If it has `apply_to_chart` (a `Primitive`) → call it with the chart; prices are available unsliced as `chart.prices`
2. Otherwise compute: call `apply_indicator(prices, item)` → full-length result. If the item is a polars Expr that evaluates to a Struct Series, it is unnested into a multi-column DataFrame so downstream code can iterate `.columns`
3. Slice: `chart.slice(result)` → restricts to the visible window via the mapper
4. Hand to `AutoPlot` for default rendering: single Series → one line; DataFrame → one trace per column (with `upperband` / `middleband` / `lowerband` and `*hist` columns getting specialized handling)

## Mapper

`DateIndexMapper` stores the full datetime array and uses **integer rownums** as matplotlib x-coordinates. This eliminates weekend/holiday gaps without any special logic. `DTArrayLocator` / `DTArrayFormatter` map tick positions back to date labels. `RawDateMapper` is an alternative that uses actual datetimes (matplotlib handles axis formatting).

## Operator conventions

`@` is the binding operator for both indicators and expressions:

| Operator | Meaning |
|---|---|
| `SMA(50) @ LinePlot(...)` | bind indicator or expression to a primitive |
| `SMA(50) \| EMA(10)` | chain indicators left-to-right |
| `prices.pipe(SMA(50))` | apply indicator to data directly (use pandas `.pipe` or call the indicator) |

## Primitives

Regular primitives (`LinePlot`, `AreaPlot`, `BarPlot`, `AutoPlot`, `Price`) use `chart.mapper.series_xy(data)` for x/y extraction. Irregular primitives (`ZigZag`, `Peaks`, `Stripes`, `Markers`) compute their own sparse row indices and index into `mapper.rownum` directly.
