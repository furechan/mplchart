# Architecture

Design notes: [axes-stickiness.md](axes-stickiness.md) — pane vs axes vocabulary and current-pane semantics. [primitive-contract.md](primitive-contract.md) — the Chart API surface primitives may use (living document). [canvas-view-rationale.md](canvas-view-rationale.md) — agreed direction: Chart = Canvas (presentation plane) + DataView (data plane), primitives converging on `apply(canvas, view)`; target interfaces in [canvas-view-sketch.md](canvas-view-sketch.md), evolution plan in [canvas-view-roadmap.md](canvas-view-roadmap.md).

Discussion (not decided): [polars-proposal.md](polars-proposal.md) — exploring a polars-only future. [styler-sketch.md](styler-sketch.md) — mplfinance-like style option (Style spec + Styler runtime under `styles/`).

## Module layout

| Module | Role |
|---|---|
| `chart.py` | `Chart` — main entry point; composes the data view (`chart.view`) and canvas (`chart.canvas`); fluent API + plotting pipeline |
| `model/primitive.py` | `Primitive` and `BindingPrimitive` — backend-agnostic base classes |
| `model/indicator.py` | `Indicator` and `IndicatorChain` — pandas-only base classes |
| `dataview.py` | `DataView` contract + backend-native `PandasDataView` / `PolarsDataView`, created via `get_view(prices, raw_dates=)`; native `eval` per subclass |
| `primitives/` | Drawing primitives — operate directly on the prices DataFrame |
| `indicators.py` | Pandas-only indicator classes (subclass `Indicator`) |
| `library.py` | Pandas-only calc functions called by indicators |
| `expressions/` | Polars-only expression factories returning `pl.Expr` (multi-output expressions return a `pl.struct(...)` Expr) |
| `utils.py` | Backend detection, `is_indicator_like`, `col_to_numpy`, `normalize_prices`, etc. (`apply_indicator` deprecated — use `view.eval`) |
| `layout.py` | Matplotlib figure/axes layout helpers |
| `canvas.py` | `Canvas` — presentation plane: figure, title, styled panes, pane state, show/render; owns the `Styler` and delegates color resolution to it |
| `styles/` | Style machinery — runtime `Styler` (color-scheme lookup, per-pane color cycles, prop-cycle sentinels, scoped rc context); target design in [styler-sketch.md](styler-sketch.md) |
| `dateaxis.py` | Date x-axis machinery — `DTArrayLocator`, `DTArrayFormatter`, `config_date_axis` |

## Backends

The core (`chart.py`, `dataview.py`, `primitives/`) is backend-agnostic. Backend-specific code is opt-in:
- `indicators.py` + `library.py` — pandas only; imported lazily
- `expressions/` — polars only; imported lazily

## Plotting pipeline

For each item passed to `chart.plot()`:
1. If it has `apply_to_chart` (a `Primitive`) → call it with the chart; prices are available unsliced as `chart.view.prices`
2. Otherwise compute: `chart.view.eval(item)` → full-length result. If the item is a polars Expr that evaluates to a Struct Series, it is unnested into a multi-column DataFrame so downstream code can iterate `.columns`
3. Window: `chart.view.series_xy(...)` cuts full-length results to the visible window (`chart.view.slice` windows the prices frame itself)
4. Hand to `AutoPlot` for default rendering: single Series → one line; DataFrame → one trace per column (with `upperband` / `middleband` / `lowerband` and `*hist` columns getting specialized handling)

## Data view

`get_view(prices, raw_dates=)` routes to a backend-native data view: `PandasDataView` (stores a tz-naive DatetimeIndex and a date-indexed `xloc` Series; slices by joining on it) or `PolarsDataView` (stores Datetime and `xloc` Series; slices positionally). Backend is the subclass axis; `raw_dates` is a mode flag deciding what `xloc` holds — integer rownums (default; eliminates weekend/holiday gaps, with `DTArrayLocator`/`DTArrayFormatter` mapping ticks back to date labels) or the datetimes themselves (matplotlib handles axis formatting). The `DataView` base is a pure contract holding no state; each backend derives dates from the prices frame natively — numpy appears only at the matplotlib boundary. Evaluation lives on the view: each subclass implements `eval(item)` in full — column strings, callables, and its native expressions (polars Expr/tuple with struct unnest; pandas Expression via the `_eval_expression` hook) — a mismatched item type raises `TypeError` instead of hitting a backend branch. The view itself is matplotlib-free: it exposes its native `dates` (DatetimeIndex / polars Series) and `Chart` wires the dateaxis machinery from it when not `raw_dates`; dateaxis coerces to numpy at its own boundary.

## Operator conventions

`@` is the binding operator for both indicators and expressions:

| Operator | Meaning |
|---|---|
| `SMA(50) @ LinePlot(...)` | bind indicator or expression to a primitive |
| `SMA(50) \| EMA(10)` | chain indicators left-to-right |
| `prices.pipe(SMA(50))` | apply indicator to data directly (use pandas `.pipe` or call the indicator) |

## Primitives

Regular primitives (`LinePlot`, `AreaPlot`, `BarPlot`, `AutoPlot`) use `chart.view.series_xy(data)` for x/y extraction. Irregular primitives (`ZigZag`, `Swings`, `Stripes`, `Markers`) compute their own sparse row indices and map them through `chart.view.slice(..., xcol=...)` or `chart.view.series_xy`. The data plane is the view and the figure plane is the canvas: primitives call `chart.view.*` (`eval`, `series_xy`, `slice`, `map_date`, `prices`) and `chart.canvas.*` (`get_axes`, `resolve_color`, `root_axes`, `main_axes`) directly — Chart wraps neither. Chart keeps only the fluent surface (`plot`, `pane`, `hline`, `vline`, `show`, `render`, `figure`, `title=`).
