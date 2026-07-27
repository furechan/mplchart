# Backlog

Items decided or considered but not scheduled. Add new items at the end.

## API

- ~~Consider a polars `merge_prices` equivalent to `mplchart.pandas.merge_prices`~~ — demoted 2026-07-26: merging is data prep, not charting; `multiple-tickers.ipynb` now shows the merge inline in both backends and `merge_prices` is deprecated — remove it (and reconsider `rebase_series`) after a release or two
- Add `metadata=` parameter to `Chart.render`/`Canvas.render` passed through to `savefig`, with merged defaults (`Title` from chart title, `Creator: mplchart`) for metadata-capable formats (svg/png/pdf/ps) — provenance, not SEO; SVG accepts only fixed Dublin Core keys, don't inject `Date` (keeps re-renders deterministic)
- Percentage (log) box sizes for `calc_renko`/`calc_pnf` (`pct=`) — a fixed dollar box distorts long histories (giant early columns, volume skew; demonstrated in the proto notebooks); run the same algorithm on `log(close)` with `size = log(1+pct)`; rendering needs a pct-aware primitive or a log y-axis (see notes/view-transforms.md)
- High/low-based PnF extension (`method="close"|"hl"`) — classical PnF extends X columns on the high and O columns on the low; calc_pnf is close-based today
- Configurable renko `reversal=` — the 2-brick reversal is implicit in the symmetric top/bottom rule; other values need explicit trend tracking in `calc_renko`
- Selective pane addresses `pane="top"` / `pane="bottom"` (visually extreme panes) — designed-for in notes/axes-stickiness.md; `"main"` is first-created, not topmost once `"above"` panes exist
- Review all primitive styling parameters that should get their own styler setting (e.g. `stripes.alpha`/`stripes.color` resolved like `candle.*`; Stripes got a plain `alpha=0.2` default 2026-07-27 as the interim fix)

## Cleanup

- ~~Pane/axes cleanup per [notes/axes-stickiness.md](notes/axes-stickiness.md)~~ — done 2026-07-26 with a simpler model than sketched: no cursor state — `Pane(position=)` creative+sticky (only creator), renderer `pane=` selective+ephemeral, disjoint vocabularies; `get_axes`/`new_axes` split at canvas level; `Pane("main")` now raises; Volume owns empty panes (dedicated volume sub-pane works)
- ~~Implement a low-level numpy-based `forward_fill` util for the identical sign/clip + NaN forward-fill blocks in `primitives/markers.py` and `primitives/stripes.py`~~ — done 2026-07-26: `forward_fill` in the new `arrays.py` module (low-level numpy utilities live there, not in `utils.py`); both primitives converted, edge cases pinned in `tests/test_arrays.py`
- Remove `mplchart.pandas.merge_prices` (deprecated in 0.0.46) and decide `rebase_series`'s fate — after a release or two of grace
