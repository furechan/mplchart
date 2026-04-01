---
name: Examples notebook structure
description: How the examples/ folder is organized after April 2026 consolidation
type: project
---

The `examples/` folder was consolidated from 29 notebooks down to 5 in April 2026.

Current structure:
- `typical-usage.ipynb` — intro / quick start, uses `sample_prices()`
- `chart-primitives.ipynb` — all display primitives (Candlesticks, OHLC, Price, Volume, LinePlot, AreaPlot, BarPlot, Markers, Stripes, ZigZag)
- `chart-indicators.ipynb` — all built-in indicators with section headers
- `chart-render.ipynb` — rendering to SVG/PNG/JPG formats
- `talib-examples.ipynb` — talib `Function` integration

**Why:** 29 one-indicator-per-file notebooks were too many for GitHub browsing. Consolidated into thematic notebooks with markdown section headers.

**How to apply:** Don't add new per-indicator notebooks. Add new indicators/primitives as sections inside the relevant consolidated notebook.
