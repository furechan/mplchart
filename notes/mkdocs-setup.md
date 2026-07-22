# MkDocs Site Setup

Documentation/tutorial site for discoverability — tutorials, articles, and a browsable gallery rather than a pdoc-style API dump (nobody searches for API symbols; they search "candlestick chart python", "plot RSI matplotlib"). Published on GitHub Pages.

## Stack

- **MkDocs Material + mkdocs-jupyter**, installed via the `docs` dependency group (`uv add --group docs`), locked in `uv.lock`. Chosen over Sphinx (heavier toolchain) and Quarto (separate non-Python binary).
- Config in `mkdocs.yml` at repo root: theme, plugins, and `nav:` (the site tree — decoupled from file locations, so pages can be repositioned by editing YAML only).
- `mkdocstrings` API reference is a possible later add-on, not the centerpiece.

## Layout

- `docs/` — site source (MkDocs default `docs_dir`). Landing page `index.md` adapted from README.
- `docs/examples` → symlink to `examples/` — notebooks stay single-source, no copies to drift. All 8 example notebooks are wired into the nav as tutorials.
- `notes/` — internal design/engineering notes (formerly `docs/`), not published.
- `site/` and `.cache/` (mkdocs-jupyter conversion cache) are gitignored; built HTML is never committed.

## Build model

- **Notebooks render from committed outputs** (`execute: false`) — no execution, no network, no yfinance flakiness at build time; builds take seconds. Executing and saving outputs is a local authoring step (`nbcheck` habit covers freshness).
- Notebook markdown cells are indexed by the built-in site search; cell tags (`hide_input`, `remove_cell`) can shape the published look later.
- Local preview: `uv run mkdocs serve` at localhost:8000, live-reloads on save; VS Code auto-forwards the port over SSH (Simple Browser works too). `uv run mkdocs build` writes `site/`.
- Publishing (TODO): GitHub Actions workflow on push to main — `uv sync --group docs` + `mkdocs build`, deployed via the Pages "GitHub Actions" source (no gh-pages branch). Nothing is published manually.

## Search/SEO notes

- Notebook chart outputs are **embedded** in the page HTML by nbconvert (base64 PNG / inline SVG) — fine for site search and Google text search, invisible to Google Images (data URIs have no URL). Applies to the gallery notebook too — accepted tradeoff: image-search referral is a negligible channel; the gallery's value is text-search landing content + chart-with-code catalog for visitors.
- Notebook chart format: settled on default PNG — see the Gallery section for the rationale and the SVG option.

## Gallery

- `docs/gallery.ipynb` — a plain notebook: setup cell (imports, `sample_prices()`), then one markdown heading + one code cell per chart. Chosen over a script-generated page for the authoring loop: edit cell, run, see the chart — plug and play. (A script-based generator with deterministic standalone SVGs was tried first and dropped 2026-07; see git history if the grid/detail-page end state ever revives it.)
- Entries: candlesticks+volume, SMA, BBANDS, RSI, MACD, STOCH, KELTNER, TrendLines. Code cell directly above each chart is the copy-paste snippet (imports live in the setup cell).
- **Pinned data**: bundled `mplchart.samples.sample_prices()` (AAPL) — no network; re-execute after `scripts/update-samples.py` changes.
- `inv gallery` re-executes the notebook in place (`jupyter nbconvert --execute --inplace`); outputs are committed like the example notebooks.
- **Chart format: default PNG**, same as the example notebooks — simplest and consistent. To force SVG, the only stable mechanism is a visible `%config InlineBackend.figure_formats = ["svg"]` setup cell per notebook — there is no project-level knob: the format is an IPython `InlineBackend` traitlet (not a matplotlib rc value), and ipykernel activates the inline backend itself, overriding any `matplotlibrc` `backend:` setting. Data point from an SVG trial (2026-07): 8 SVG charts ≈ 2.3 MB built page vs 18 PNG charts ≈ 2.4 MB (primitives-pandas) — SVG ~2× heavier per chart uncompressed but gzips well and stays crisp on hi-dpi; revisit per-notebook if PNG sharpness disappoints on the published site.

## Examples restructure (in progress, 2026-07)

With the gallery in place, the per-item parade notebooks (indicators-pandas, primitives-pandas/polars, expressions-polars) are redundant — the backend-duplicated pairs exist to show parity, which is a test concern (`test_backend_parity.py`), not a docs concern. Target: mechanics notebooks organized by concept, one backend each, breadth moves to the gallery.

- **Done**: `examples/indicators.ipynb` — indicator mechanics (callables, panes, binding constructor-first with `@` alternative, `|` chaining, `as_expr` boolean composition, custom via bare function or `Indicator` subclass).
- **Done**: `examples/expressions.ipynb` — expression mechanics (factories return aliased native `pl.Expr`, struct multi-output, `src` composition instead of `|`, native boolean conditions, custom via `.alias()` or `wrap_expression`). Mirrors the indicators page section-for-section.
- **Done**: removed `indicators-pandas.ipynb` and `expressions-polars.ipynb` after harvesting their unique charts into the gallery (DONCHIAN, DMI, MACDV, BBP/BBW — gallery now 12 charts).
- **Done**: `examples/primitives.ipynb` — primitive mechanics organized by role (price/volume renderers with color options, indicator renderers `LinePlot`/`AreaPlot`/`BarPlot`, condition primitives `Stripes`/`Markers`, `Pane`/`HLine`/`VLine`, pattern primitives `Swings`/`ZigZag`/`TrendLines`), with backend-parity note. Replaces both primitives parades (removed).
- **TODO**: backend-architecture article (plain md): what's shared, pandas-only (indicators), polars-only (expressions).

## Publishing

`.github/workflows/docs.yml` deploys on push to main: `uv sync --only-group docs` (nbcheck + mkdocs only — no ta-lib/numba, notebooks render from committed outputs), `nbcheck -x examples docs` (refuses to deploy unexecuted/cleared notebooks), `mkdocs build --strict`, then Pages artifact deploy. Pages source must be set to "GitHub Actions" in repo settings. Stale-notebook guard also runs locally via `inv check`.

## Next steps

1. More articles (how panes work, custom indicators).
2. Gallery growth: more entries, then detail pages/thumbnail grid if the single page gets heavy.
3. README: add a documentation link to the site once live.
