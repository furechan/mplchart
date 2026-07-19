---
name: Examples notebook structure
description: How the examples/ folder is organized after April 2026 consolidation
type: project
---

The `examples/` folder was consolidated from 29 notebooks down to a handful in April 2026. The `chart-` filename prefix was dropped in July 2026.

Current structure (8 notebooks):
- `typical-usage.ipynb` — quickstart landing page
- `indicators-pandas.ipynb` — indicator catalog (pandas)
- `expressions-polars.ipynb` — expression catalog (polars)
- `primitives-pandas.ipynb` — display primitives with pandas backend
- `primitives-polars.ipynb` — display primitives with polars backend
- `chart-render.ipynb` — render to SVG / PNG / JPG via `chart.render()`
- `multiple-tickers.ipynb` — multi-ticker overlay via `merge_prices` (pandas-only; polars equivalent is backlogged)
- `talib-functions.ipynb` — ta-lib `Function` integration

`examples/README.md` is the index table; the main README's `## Examples` section links to it.

**Why:** 29 one-indicator-per-file notebooks were too many for GitHub browsing. Consolidated into thematic notebooks with markdown section headers.

**How to apply:** Don't add new per-indicator notebooks. Add new indicators/primitives as sections inside the relevant consolidated notebook. Keep `examples/README.md` in sync when adding or renaming notebooks.
