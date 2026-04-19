---
name: Examples notebook structure
description: How the examples/ folder is organized after April 2026 consolidation
type: project
---

The `examples/` folder was consolidated from 29 notebooks down to a handful in April 2026.

Current structure (8 notebooks):
- `typical-usage.ipynb` — quickstart landing page, includes a backend-routing nav table at the bottom
- `chart-indicators.ipynb` — indicator catalog (pandas); has a 1-line backend note linking to the polars equivalent
- `chart-expressions.ipynb` — expression catalog (polars); has a 1-line backend note linking to the pandas equivalent
- `chart-primitives-pandas.ipynb` — display primitives with pandas backend (indicators + `|`)
- `chart-primitives-polars.ipynb` — display primitives with polars backend (expressions + `@`)
- `chart-render.ipynb` — render to SVG / PNG / JPG via `chart.render()`
- `compare-tickers.ipynb` — multi-ticker overlay via `mplchart.pandas.merge_prices` (pandas-only; polars equivalent is backlogged)
- `talib-examples.ipynb` — ta-lib `Function` integration

README has a matching `## Examples` section with a pandas/polars × catalog/primitives table.

**Why:** 29 one-indicator-per-file notebooks were too many for GitHub browsing. Consolidated into thematic notebooks with markdown section headers.

**How to apply:** Don't add new per-indicator notebooks. Add new indicators/primitives as sections inside the relevant consolidated notebook.
