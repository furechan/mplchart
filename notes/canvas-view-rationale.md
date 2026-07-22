# Canvas / View Split

Design note (direction agreed 2026-07-19, not yet implemented). Decomposes `Chart` into two first-class planes — a presentation plane (**Canvas**) and a data plane (**View**) — with primitives ultimately converging on `apply(canvas, view)`.

Companions: [canvas-view-sketch.md](canvas-view-sketch.md) — the target API reference; [canvas-view-roadmap.md](canvas-view-roadmap.md) — the evolution plan. This note is the rationale.

Related: [primitive-contract.md](primitive-contract.md) (the current contract this design restructures), [axes-stickiness.md](axes-stickiness.md) (pane semantics the Canvas absorbs), [polars-proposal.md](polars-proposal.md) (whose urgency this design reduces).

## Motivation

In a classic plotting package the interface is `indicator.render(ax, prices)` — and mplchart's own API looked like that for a while. This design is the same split, upgraded one level:

| Classic | Upgraded | What the upgrade adds |
|---|---|---|
| `ax` | **Canvas** | paned, styled, stateful drawing surface: root/pane axes, height ratios, twinx, current-pane stickiness, color scheme |
| `prices` | **View** | ranged frame with coordinate context: window (start/end/max_bars), per-row x-coordinates (xloc), date↔x mapping, native evaluation |
| `render` | `apply` | the old `render` both computed and drew; the new shape puts evaluation on the View and drawing in the primitive |

The immediate driver is low-level experimentation: generate a figure, some panes, a configured x-axis, and plot natively — without the Chart engine. The end state makes that first-class:

```python
canvas = Canvas(figsize=(12, 9))
view = get_view(prices, max_bars=250)
Candlesticks().apply(canvas, view)     # no Chart, no shim, no fake host
```

`Chart` remains as the batteries-included fluent wrapper (`plot()`, `pane()`, title, legends, color scheme defaults) — pure sugar over the exact calls you'd write by hand. Same machinery, two entry altitudes.

## Layers

| Layer | Home | Contents | Imports |
|---|---|---|---|
| Presentation plane | **Canvas** | figure factory, styled panes (root x-grid / pane y-grid split, zero xmargin, right yticks), height ratios, twinx, current-pane stickiness, color resolution (`get_color`, scheme, per-axes cycling) | matplotlib only — never sees a frame |
| Data plane | **View** | prices frame + window, `window()`, `series_xy()`, `map_date()`, `dates`, `raw_dates`, `eval()` | backend-native — **zero matplotlib** |
| Axis machinery | **dateaxis** | `DTArrayLocator`, `DTArrayFormatter`, `config_date_axis(ax, dates)` | matplotlib + numpy |
| Composition | **Chart** | owns a Canvas and a View; fluent API; plot pipeline; wires `config_date_axis` when not `raw_dates` | all of the above |

Dependencies point strictly downward: Chart → {Canvas, View, wiring}; wiring → locators/formatters; Canvas and View → nothing of each other. The View being matplotlib-free is a protected property — it makes the data plane testable without a figure and portable to any renderer.

## The View

The mapper (`DateMapper` / `PandasDateMapper` / `PolarsDateMapper`) renamed — `DataView`, subclasses `PandasDataView` / `PolarsDataView`, factory `get_view` — and promoted to what it already is: a ranged view on the prices frame. It wraps the frame (composition, explicit surface — **no** `__getattr__` forwarding of the dataframe API) and adds context: window, xloc, date↔x mapping.

| Member | Contract |
|---|---|
| `prices` | the wrapped full-length frame, native backend |
| `window(item=None)` | `None` → windowed prices with the `xloc` column materialized (absorbs today's `slice(prices, xcol="xloc")` idiom — the only form ever used); an item → evaluated full-length, then windowed with xloc (frame-shaped results) |
| `series_xy(*items_or_series)` | fused compute-and-window: item-like arguments are evaluated first (full-length), then everything is windowed together → `(x, *windowed)` numpy arrays; full-length series pass through as today, length enforced |
| `map_date(date)` | date → x-coordinate |
| `dates` | native datetime array-like — feeds `config_date_axis`, which coerces to numpy at its own boundary |
| `raw_dates` | mode flag: what xloc holds (rownums vs datetimes); read by the composition layer to decide wiring |
| `eval(item)` | evaluation hook underneath the fused forms: evaluate an indicator/expression against `prices` → **full-length** native result; primitives mostly call the fused forms instead |

### Evaluation lives on the View

`apply_indicator`'s dispatch moves into the View, split along the subclass axis — dispatch by subclass replaces dispatch by inspection:

- Each subclass implements `eval` in full — column string, callable, and its native expression types; no shared template (pandas deals with pandas, polars with polars).
- **`PolarsDataView`**: `pl.Expr` → `select` (struct → unnested frame), tuple of Expr → frame. Needs only polars itself — `expressions/` *creates* Exprs; the View merely evaluates them.
- **`PandasDataView`**: pandas Expression via the duck-typed `_eval_expression` hook (detected via `type(item).__dict__`) — no import of the expression module.

The backend branch doesn't move — it disappears. A polars Expr reaching a `PandasDataView` is not a checked branch but a type the receiving view doesn't recognize. No opt-in module leaks into the core: evaluation is item-shape duck-typing plus native frame ops.

Rejected alternatives, for the record:

- `chart.calc_result` (status quo) — evaluation is not chart policy; no chart state affects it (the `last_result` cache, the one piece of state, was removed 2026-07-18). It only lived on Chart because `prices` did.
- Free function `apply_indicator(prices, item)` — keeps a backend × item-type inspection branch forever, and is a hidden third dependency in every data-bearing primitive, breaking the closure of `apply(canvas, view)`.

### Design rule: orderings are fixed by semantics, not call-site syntax

The two compute/window orderings from [primitive-contract.md](primitive-contract.md) are both semantic and both preserved — but by contract definition, not by keeping the steps syntactically separate:

- Analytics: **evaluation always computes on the full series**, then the fused forms return the visible range — `view.series_xy(SMA(50))` means "compute SMA on the whole series, give me the values in range" (warmup depends on history before the window). This is well-defined the same way rolling semantics are; no ambiguity to protect against.
- Geometry: window first, then kernel — `view.window()` → kernel (pivots near the window edge depend on the window). A separate idiom on a separate method; eval is never involved.

Fusing compute-and-window is safe because of an empirical property the contract audit already recorded: everything primitives do between evaluation and windowing today (column selection, pointwise transforms like Markers' `clip(sign(...))`) **commutes with windowing** — never a filter, sort, dropna, or resample. Nothing can observe which side of the window it ran on. Markers under the fused form: `x, sig, close = view.series_xy(ind, "close")`, transform applied after. Fusion also points the same direction as the contract doc's frame-model future ("in a frame model the variadic form disappears").

## The Canvas

Green-field object absorbing what today is scattered across `layout.py` and Chart methods:

- Figure creation (tight layout, figsize) and the root axes.
- Pane creation with styling: `Chart.config_axes` is stateless and moves here (root draws the x-grid, panes draw y-grids, zero xmargin, right-side yticks, hidden pane x-ticks).
- `add_vplot` / `make_twinx` geometry, height ratios.
- Current-pane stickiness (see [axes-stickiness.md](axes-stickiness.md)) — mutable state, Canvas-owned.
- Color machinery: `color_scheme`, `get_color`, per-axes cycling counters. Colors are presentation policy.

The Canvas never sees a dataframe. Numpy arrays cross the boundary; frames don't.

## Primitive contract endgame

The contract migrates from "chart implements a fat surface" to `apply(canvas, view)` — **closed** over its two parameters: a primitive needs those objects and nothing else, not even a blessed import.

Mapping from the current [primitive-contract.md](primitive-contract.md) surface:

| Today | End state |
|---|---|
| `chart.series_xy`, `chart.slice`, `chart.prices`, `chart.map_date` | `view.series_xy`, `view.window()`, `view.prices`, `view.map_date` |
| `chart.calc_result` | `view.eval` — though most `calc_result` + `series_xy` pairs collapse into the fused `view.series_xy(item)` |
| `chart.get_axes`, `chart.get_color`, `chart.root_axes`, `chart.main_axes` | `canvas.*` |

The old rule "primitives never touch `chart.mapper`" inverts rather than carrying over: the mapper was hidden as an implementation detail; the View is exposed as the designed interface — *the supported way to touch data*.

## Backends

The pandas/polars split stops being an architecture question and gets confined to exactly one place each:

- Windowing/coordinates/evaluation: the View subclass (`PandasDataView` / `PolarsDataView`). Callers never see the backend; numpy appears only at the matplotlib boundary.
- Item creation: the opt-in modules (`indicators.py`/`library.py` pandas-only, `expressions/` polars-only) — a fact about items, not about the core.

Canvas and primitives are backend-blind. Consequence for [polars-proposal.md](polars-proposal.md): going polars-only would mean deleting a View subclass and its eval cases, not restructuring the core — the decision becomes cheap and deferrable.

## Migration order

Contract written as the end state, migrated via the composite, in four phases: **DataView** (dateaxis extraction, mapper rename, eval in, wiring out) → **Canvas** (built under Chart) → **contract restated** (primitives touch only `chart.view` / `chart.canvas`) → **signature flip** (`apply(canvas, view)`; the flip is optional — phase 3 already delivers the contract in substance). Step-by-step plan with deprecation ledger: [canvas-view-roadmap.md](canvas-view-roadmap.md).
