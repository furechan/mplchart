# Primitive naming conventions

Status: `LinePlot` → `Line`, `AreaPlot` → `Area`, and `BarPlot` → `Bars` implemented with legacy warning subclasses. `Candlesticks` and `AutoPlot` retain their names. Package-root access and a documented namespace alias remain under discussion.

The sections below preserve the options discussed before the decision. Legacy wrappers use `__new__` and inherit the canonical initializer; construction and copying/binding emit `DeprecationWarning`. Both package exports and the existing implementation-module imports remain available. No removal release has been selected.

## Namespace access comes first

Before shortening names, establish convenient namespace access. Generic names such as `Line`, `Area`, and `Bar` occur in many libraries; users should not need to import them individually into their own scope.

Plotly offers a useful analogy: `plotly.express as px` is the high-level function API, while `plotly.graph_objects as go` is the closer parallel to mplchart's composable primitive objects. The user rejected the suggested one-letter alias `p` as insufficiently memorable or specific. `prim` was then suggested as a documented shorthand for the existing `primitives` subpackage; using `primitives` without an alias is also an option. Neither requires adding a new alias module.

The latest proposal is to expose `Chart` at the package root while keeping the primitive family in its subpackage:

```python
from mplchart import Chart
from mplchart import primitives as prim
from mplchart.indicators import SMA

chart = Chart(prices)
chart.plot(prim.Candlesticks(), prim.Line(SMA(50)))
```

This illustrates a proposed API, not the current implementation or an agreed naming decision. Root access to `Chart` would make the main entry point easy to discover without requiring knowledge of `mplchart.chart`; the primitive namespace would qualify generic names without exporting the whole family at the root. Alternatives discussed were `import mplchart as mc` with all primitives at the root, and access through the existing submodules. Settle the public import surface and documented shorthand before choosing the shorter class names.

## Proposed names

Consider shortening `LinePlot`, `AreaPlot`, and `BarPlot` to `Line`, `Area`, and `Bar` or `Bars`. Also consider whether `Candlesticks` should become `Candlestick`. `AutoPlot` would retain its name because it describes automatic rendering selection.

Two possible vocabularies emerged:

- Chart types: `Line`, `Area`, `Bar`, `Candlestick`.
- Drawn elements: `Line`, `Area`, `Bars`, `Candlesticks`, alongside existing `Markers`, `Bands`, and `Stripes`.

Counting shapes does not settle the question: `Line` is the natural conventional name even though rendering connects many individual line segments. Nor does consistency necessarily require every primitive to have the same grammatical number. The user identified Plotly as the closest vocabulary, with the singular/plural difference still unresolved.

## Library precedents

These are conventions, not a universal standard:

| Library | Relevant API names |
|---|---|
| [Plotly graph objects](https://plotly.com/python-api-reference/plotly.graph_objects.html) | `Bar`, `Candlestick`, `Ohlc`; lines and filled areas use `Scatter` |
| [TradingView Lightweight Charts](https://tradingview.github.io/lightweight-charts/docs/series-types) | `LineSeries`, `AreaSeries`, `BarSeries`, `CandlestickSeries`, `HistogramSeries` |
| [Bokeh](https://docs.bokeh.org/en/latest/docs/reference/plotting/figure.html) | `line()`, `varea()`, `vbar()`, `hbar()` |
| [HoloViews](https://holoviews.org/reference_manual/holoviews.element.chart.html) | `Curve`, `Area`, `Bars`, `Scatter` |
| [mplfinance](https://github.com/matplotlib/mplfinance) | Chart types `line`, `candle`, `ohlc`, `renko`, `pnf` |

TradingView's `BarSeries` means OHLC bars; rectangular value bars use `HistogramSeries`. Plotly does not provide a direct `Line`/`Area` trace-class naming template.

## Compatibility options

The discussion initially considered direct renames, then retaining legacy names during a transition:

- Plain aliases such as `LinePlot = Line` preserve class identity but do not warn on access.
- Module-level `__getattr__` can return the canonical class and warn when an old name is requested. This preserves identity but requires handling compatibility at the module boundary.
- Small legacy subclasses can warn when instantiated, then be deleted after the transition. The user favored considering this explicit approach because there are only a few classes. Legacy instances are instances of the new base class, but the classes have distinct identities.

For subclasses, a generic `__init__(*args, **kwargs)` warning wrapper conflicts with the existing `short_repr`, which inspects `__init__` signatures. Either preserve the explicit initializer signature or consider putting the warning in `__new__` and inheriting `__init__` unchanged:

```python
class LinePlot(Line):
    """Deprecated: use Line."""

    def __new__(cls, *args, **kwargs):
        warnings.warn(
            "LinePlot is deprecated; use Line instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().__new__(cls)
```

This is a sketch, not an adopted implementation. Python calls the inherited initializer with the original arguments. `__new__` may also run during copying or unpickling, causing additional warnings; review this against primitive cloning and `@` binding. Check class-level signature introspection separately from `short_repr`'s inspection of `__init__`.

## Review before implementation

- Settle namespace access first: whether to expose `Chart` at the root, keep primitives under `mplchart.primitives`, and document `prim` as the shorthand.
- Choose the canonical names, especially `Bar` versus `Bars` and `Candlestick` versus `Candlesticks`.
- Decide whether to retain legacy names, and whether they are merely supported aliases or deprecated APIs scheduled for removal.
- If using warning subclasses, verify signatures, repr, cloning/binding, and warning behavior.
- Define the supported import paths and transition/removal policy.
- Update maintained callers, examples, generated API documentation, and the changelog if the rename proceeds; preserve prototype notebooks as historical artifacts.
