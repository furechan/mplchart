# Architecture

Design notes: [axes-stickiness.md](axes-stickiness.md) — pane vs axes vocabulary and current-pane semantics. [primitive-contract.md](primitive-contract.md) — the Chart API surface primitives may use (living document).

Discussion (not decided): [polars-proposal.md](polars-proposal.md) — exploring a polars-only future.

## Module layout

| Module | Role |
|---|---|
| `chart.py` | `Chart` — main entry point; owns the figure, mapper, and plotting pipeline |
| `model/primitive.py` | `Primitive` and `BindingPrimitive` — backend-agnostic base classes |
| `model/indicator.py` | `Indicator` and `IndicatorChain` — pandas-only base classes |
| `mapper.py` | `DateMapper` contract + backend-native `PandasDateMapper` / `PolarsDateMapper`, created via `get_mapper(prices, raw_dates=)` |
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
3. Window: `chart.series_xy(...)` cuts full-length results to the visible window (`chart.slice` windows the prices frame itself)
4. Hand to `AutoPlot` for default rendering: single Series → one line; DataFrame → one trace per column (with `upperband` / `middleband` / `lowerband` and `*hist` columns getting specialized handling)

## Mapper

`get_mapper(prices, raw_dates=)` routes to a backend-native mapper: `PandasDateMapper` (stores a tz-naive DatetimeIndex and a date-indexed `xloc` Series; slices by joining on it) or `PolarsDateMapper` (stores Datetime and `xloc` Series; slices positionally). Backend is the subclass axis; `raw_dates` is a mode flag deciding what `xloc` holds — integer rownums (default; eliminates weekend/holiday gaps, with `DTArrayLocator`/`DTArrayFormatter` mapping ticks back to date labels) or the datetimes themselves (matplotlib handles axis formatting). The `DateMapper` base is a pure contract holding no state; each backend derives dates from the prices frame natively — numpy appears only at the matplotlib boundary.

## Operator conventions

`@` is the binding operator for both indicators and expressions:

| Operator | Meaning |
|---|---|
| `SMA(50) @ LinePlot(...)` | bind indicator or expression to a primitive |
| `SMA(50) \| EMA(10)` | chain indicators left-to-right |
| `prices.pipe(SMA(50))` | apply indicator to data directly (use pandas `.pipe` or call the indicator) |

## Primitives

Regular primitives (`LinePlot`, `AreaPlot`, `BarPlot`, `AutoPlot`) use `chart.series_xy(data)` for x/y extraction. Irregular primitives (`ZigZag`, `Swings`, `Stripes`, `Markers`) compute their own sparse row indices and map them through `chart.slice(..., xcol=...)` or `chart.series_xy`. Primitives never touch `chart.mapper` directly — the mapper is an implementation detail behind the `Chart` data-plane methods (`slice`, `series_xy`, `map_date`).
