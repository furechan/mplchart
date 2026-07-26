---
name: project-examples-structure
description: How the examples/ folder is organized — mechanics notebooks + gallery (July 2026 restructure)
metadata:
  type: project
---

The `examples/` folder was consolidated from 29 notebooks to a handful in April 2026, then restructured in July 2026 when the MkDocs site + gallery landed: the per-item "parade" notebooks (indicators-pandas, expressions-polars, primitives-pandas, primitives-polars) were removed in favor of concept-organized *mechanics* notebooks, one backend each — visual breadth lives in the gallery (`docs/gallery.ipynb`), backend parity is a test concern (`test_backend_parity.py`), not a docs concern.

Current notebooks (7):
- `typical-usage.ipynb` — quickstart landing page
- `indicators.ipynb` — indicator mechanics (callables, panes, binding, `|` chaining, `as_expr`, custom indicators; pandas)
- `expressions.ipynb` — expression mechanics (factories, `src` composition, boolean conditions, `wrap_expression`; polars); mirrors the indicators page section-for-section
- `primitives.ipynb` — primitive mechanics by role (price/volume renderers, chart types — HeikinAshi/Renko/PointFigure incl. the transform-first contract, indicator renderers, condition primitives, panes/reference lines, pattern primitives); backend-agnostic
- `chart-render.ipynb` — render to SVG / PNG / JPG via `chart.render()`
- `multiple-tickers.ipynb` — multi-ticker overlay via `merge_prices` (pandas-only; polars equivalent is backlogged)
- `talib-functions.ipynb` — ta-lib `Function` integration

There is deliberately no `examples/README.md` (removed 2026-07-26 — it duplicated the notebook listing below the fold on GitHub and was an unlinked orphan on the site; the mkdocs sidebar nav *is* the examples index — do not recreate it). The main README's `## Examples` section links to the docs-site Tutorials (absolute URL). The docs site renders these notebooks via the `docs/examples` symlink; nav in `mkdocs.yml`. Site/docs conventions live in `notes/mkdocs-setup.md`.

**How to apply:** Don't add per-indicator notebooks or backend-duplicated pairs — mechanics content goes in the concept notebooks, visual breadth in `docs/gallery.ipynb`. Update the `mkdocs.yml` nav when adding or renaming notebooks.
