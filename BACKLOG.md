# Backlog

Items decided or considered but not scheduled. Add new items at the end.

## API

- ~~Consider a polars `merge_prices` equivalent to `mplchart.pandas.merge_prices`~~ — demoted 2026-07-26: merging is data prep, not charting; `multiple-tickers.ipynb` now shows the merge inline in both backends and `merge_prices` is deprecated — remove it (and reconsider `rebase_series`) after a release or two
- Add `metadata=` parameter to `Chart.render`/`Canvas.render` passed through to `savefig`, with merged defaults (`Title` from chart title, `Creator: mplchart`) for metadata-capable formats (svg/png/pdf/ps) — provenance, not SEO; SVG accepts only fixed Dublin Core keys, don't inject `Date` (keeps re-renders deterministic)

## Cleanup

- Pane/axes cleanup per [notes/axes-stickiness.md](notes/axes-stickiness.md): add `_current_axes` with `get_axes` (pure resolver) / `set_axes` (mover) split; make `pane()`/`Pane` sugar over `set_axes` (dedup); fixes `Pane("main")` silent no-op. (`target=` removal from plot/LinePlot/AreaPlot/BarPlot: done 2026-07)
- Implement a low-level numpy-based `forward_fill` util for the identical sign/clip + NaN forward-fill blocks in `primitives/markers.py` and `primitives/stripes.py`

