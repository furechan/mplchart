# Backlog

Items decided or considered but not scheduled. Add new items at the end.

## API

- Consider a polars `merge_prices` equivalent to `mplchart.pandas.merge_prices` — would unblock a polars version of `compare-tickers.ipynb`

## Cleanup

- Pane/axes cleanup per [docs/axes-stickiness.md](docs/axes-stickiness.md): add `_current_axes` with `get_axes` (pure resolver) / `set_axes` (mover) split; make `pane()`/`Pane` sugar over `set_axes` (dedup); fixes `Pane("main")` silent no-op. (`target=` removal from plot/LinePlot/AreaPlot/BarPlot: done 2026-07)
- Implement a low-level numpy-based `forward_fill` util for the identical sign/clip + NaN forward-fill blocks in `primitives/markers.py` and `primitives/stripes.py`
- Clarify `Candlesticks` color / fill semantics: `coloroff = self.colorup or facecolor` intentionally switches up-bars from hollow to solid-filled when a custom `colorup` is set, but that is confusing and undocumented — consider an explicit hollow/filled setting and document the color params

