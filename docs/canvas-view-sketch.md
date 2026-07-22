# Canvas / View — Target API Sketch

Speculative reference (2026-07-19): the target interfaces for the [canvas-view-rationale.md](canvas-view-rationale.md) design. Preliminary and revisable — this note is the reference to steer by, not a commitment; signatures may shift as the [roadmap](canvas-view-roadmap.md) lands. Rationale lives in [canvas-view-rationale.md](canvas-view-rationale.md); this note is interfaces only.

## Canonical usage (no Chart)

```python
from mplchart.canvas import Canvas
from mplchart.dataview import get_view

canvas = Canvas(figsize=(12, 9))
view = get_view(prices, max_bars=250)

Candlesticks().apply(canvas, view)          # primitives, Chart-less
ax = canvas.get_axes("below")               # or plot natively
ax.plot(*view.series_xy(SMA(50)))
```

`Chart` remains the fluent wrapper composing the two (see bottom).

## DataView (data plane)

Module `dataview.py` — the mapper renamed and promoted. Backend is the subclass axis; **zero matplotlib imports**.

```python
def get_view(prices, *, raw_dates=False, start=None, end=None, max_bars=None) -> DataView: ...

class DataView(ABC):                # PandasDataView | PolarsDataView
    prices: Frame                   # wrapped full-length frame, native backend
    raw_dates: bool                 # what xloc holds: rownums (False) or datetimes (True)

    dates: Any                      # native datetime array-like (DatetimeIndex / pl.Series)
                                    # feeds dateaxis, which coerces to numpy at its boundary

    def window(self, item=None):    # None → windowed prices + xloc column
        ...                         # item → eval'd full-length, then windowed + xloc (frame-shaped)

    def series_xy(self, *items_or_series):   # fused compute-and-window
        ...                         # item-likes eval'd full-length; everything windowed together
                                    # → (x, *values) numpy arrays; full-length series pass through

    def eval(self, item):           # building block: full-length native result, no windowing
        ...

    def map_date(self, date):       # date → x-coordinate
        ...
```

### eval dispatch (per subclass)

| Case | Where | Behavior |
|---|---|---|
| `str` | both views | native column access (`prices[name]`) |
| `callable` | both views | called with `prices`; result unchecked (checked after native expressions — pandas Expressions are callable) |
| `pl.Expr` | `PolarsDataView` | `select`; Struct → unnested frame |
| `tuple[pl.Expr]` | `PolarsDataView` | multi-column frame |
| pandas Expression | `PandasDataView` | duck-typed `_eval_expression` hook (via `type(item).__dict__`) |
| anything else | — | `TypeError` — the receiving view doesn't recognize it (no backend branch) |

Each subclass implements `eval` in full — no shared template; pandas deals with pandas, polars with polars. The base declares the abstract contract only.

### Composition rules

- `eval` always computes on the **full** series (warmup); the fused forms return the visible range. Both altitudes are public: the fused forms are the common case; `eval` + `window()` compose freely for advanced primitives that slice at their own discretion (e.g. a future trendlines primitive) — the geometry rule (window-then-kernel for structure studies) is composition guidance, not enforced.
- No `__getattr__` forwarding of the dataframe API — explicit surface only; reach the frame via `.prices`.
- Returns cross to numpy only at the matplotlib boundary: `series_xy` returns numpy; `window()`/`eval`/`dates` stay native (dateaxis coerces `dates` itself on entry).

## Canvas (presentation plane)

Module `canvas.py` — figure + styled panes + pane state + colors. Never sees a frame.

```python
class Canvas:
    def __init__(self, figsize=None, *, figure=None, title=None, color_scheme=()): ...
                                    # creates (or adopts) the figure, tight layout, styled root axes

    def set_title(self, title): ...         # title on the root axes, above the main pane
    def add_legends(self): ...              # legends on all axes with labeled artists
    def show(self): ...                     # pyplot show
    def render(self, format="svg", *, dpi="figure") -> bytes: ...   # figure → image bytes

    figure: Figure
    color_scheme: dict

    def root_axes(self) -> Axes: ...        # background axes: x-grid, spans all panes
    def main_axes(self) -> Axes: ...        # first data pane
    def get_axes(self, target=None, *, height_ratio=None) -> Axes: ...
                                    # target: "main" | "same" | "twinx" | "above" | "below"
                                    # creates styled panes on demand; owns current-pane stickiness

    def get_color(self, name, ax=None, *, fallback=None): ...
                                    # scheme lookup (raw name, then prefix), list cycling,
                                    # "~" closest-color, "line"/"fill" dynamic fallback
```

Absorbed internals (not public surface): `init_vplot`/`add_vplot`/`make_twinx` geometry from `layout.py`; the root/pane styling from `Chart.config_axes` (root draws x-grid, panes draw y-grid, zero xmargin, right yticks, hidden pane x-ticks); per-axes color cycling counters.

## dateaxis (axis machinery)

Module `dateaxis.py` — consolidates `locators.py` + `formatters.py` + the wiring. Matplotlib + numpy only.

```python
class DTArrayLocator(mticker.Locator): ...      # ticks from a datetime64 array
class DTArrayFormatter(mticker.Formatter): ...  # labels from a datetime64 array

def config_date_axis(ax, dates): ...          # install locator + formatter on ax.xaxis
```

Coercion happens here, in exactly one place: `as_dtarray(dates)` turns any datetime array-like (DatetimeIndex, polars Series, numpy array) into a tz-naive `datetime64[s]` array. `config_date_axis` coerces once and hands the same array to locator and formatter; the constructors also coerce for standalone use (a no-op on already-coerced input).

## Chart (composition)

```python
class Chart:
    def __init__(self, prices, *, title=None, max_bars=None, start=None, end=None,
                 figure=None, figsize=None, normalize=False, raw_dates=False, color_scheme=()):
        self.view = get_view(prices, raw_dates=raw_dates, start=start, end=end, max_bars=max_bars)
        self.canvas = Canvas(figsize=figsize, figure=figure, color_scheme=color_scheme)
        if not self.view.raw_dates:
            config_date_axis(self.canvas.root_axes(), self.view.dates)
```

Fluent surface unchanged (`plot`, `pane`, `hline`, `vline`, `show`, `render`) — sugar over canvas/view calls plus pipeline conveniences (ensure main pane, legends). `plot_indicator` dispatches to the primitive contract below.

## Primitive contract (end state)

```python
class Primitive:
    def apply(self, canvas, view): ...   # closed: needs these two objects and nothing else
```

`apply_to_chart(chart)` survives as a deprecation shim: `self.apply(chart.canvas, chart.view)`.

## Open questions

- Pane-creation vocabulary: keep `get_axes(target)` as-is, or split creation (`add_pane`) from selection — revisit when Canvas is built.
- `window(item)` return shape for single-series items (frame with xloc + value column, or stay series_xy-only for series-shaped results).
- Whether dateaxis should eventually consume the view directly (`config_date_axis(ax, view)`) instead of the `dates` array — for now the surface between them is `dates`.
- Re-ranging (`view.set_range(...)` or cheap re-derive) for interactive zoom — enabled by the design, not yet specified.
- Whether `get_color` stays AutoPlot-only or explicit primitives adopt the scheme (open asymmetry noted in [primitive-contract.md](primitive-contract.md)).
