# API reference

Classic technical analysis stock charts in Python, built on matplotlib.

The pages in this section are generated from the source docstrings by `scripts/make-api-docs.py`.

## Modules

- [mplchart.chart](chart.md) — the `Chart` class: plotting, panes, rendering
- [mplchart.primitives](primitives.md) — drawing primitives: price renderers, indicator renderers, overlays, and layout controls
- [mplchart.indicators](indicators.md) — technical analysis indicators for the pandas pipeline, named `SMA`, `EMA`, etc.
- [mplchart.expressions](expressions.md) — polars expression factories, the polars-pipeline counterparts of the indicators
- [mplchart.styles](styles.md) — chart styling: the runtime `Styler` and its spec forms

See also [Pandas and polars backends](../backends.md) for how the two data pipelines relate.

## Conventions

- `prices` is a pandas or polars DataFrame with columns `open`, `high`, `low`, `close`, `volume` (lower case; use `Chart(normalize=True)` to normalize other layouts)
- Indicators and expressions use upper case names: `SMA`, `EMA`, `MACD`
- An indicator or expression is plotted directly (auto-plotted) or bound to a renderer primitive: `LinePlot(SMA(50))` or the equivalent operator form `SMA(50) @ LinePlot()`
- Indicators chain with the `|` operator: `EMA(20) | ROC(1)`
