# Backlog

Items decided or considered but not scheduled. Add new items at the end.

## API

- Add `metadata=` parameter to `Chart.render`/`Canvas.render` passed through to `savefig`, with merged defaults (`Title` from chart title, `Creator: mplchart`) for metadata-capable formats (svg/png/pdf/ps) — provenance, not SEO; SVG accepts only fixed Dublin Core keys, don't inject `Date` (keeps re-renders deterministic)
- Percentage (log) box sizes for `calc_renko`/`calc_pnf` (`pct=`) — a fixed dollar box distorts long histories (giant early columns, volume skew; demonstrated in the proto notebooks); run the same algorithm on `log(close)` with `size = log(1+pct)`; rendering needs a pct-aware primitive or a log y-axis (see notes/view-transforms.md)
- High/low-based PnF extension (`method="close"|"hl"`) — classical PnF extends X columns on the high and O columns on the low; calc_pnf is close-based today
- Configurable renko `reversal=` — the 2-brick reversal is implicit in the symmetric top/bottom rule; other values need explicit trend tracking in `calc_renko`
- Selective pane addresses `pane="top"` / `pane="bottom"` (visually extreme panes) — designed-for in notes/axes-stickiness.md; `"main"` is first-created, not topmost once `"above"` panes exist
- Review all primitive styling parameters that should get their own styler setting (e.g. `stripes.alpha`/`stripes.color` resolved like `candle.*`; Stripes got a plain `alpha=0.2` default 2026-07-27 as the interim fix)

## Cleanup

- Fold `model/` into its consumers: `model/primitive.py` → `primitives/base.py`, `Indicator`/`IndicatorChain` → `indicators.py` (or sibling module) — each model module has exactly one consumer (core duck-types), the central package blurs the pandas/backend-agnostic split, and expressions already keep their machinery local (`prelude.py`); internal-only paths, no API break; update `notes/architecture.md`
