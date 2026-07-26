# Prices Transforms & Deferred View

Design sketch (2026-07-25): how renko and point-and-figure map onto the model, and the deferred-view pattern that carries them. Discussion-stage — agreed direction, not yet implemented.

## The distinction: row-aligned vs domain transform

Heikin-Ashi is *row-aligned* — one output bar per price bar — so it works as an indicator bound to `Candlesticks` through `view.eval` + `slice` (see `primitives/heikinashi.py`).

Renko and PnF are *domain transforms*: a big-move day emits several bricks, a quiet week emits none. Output length and domain differ from the prices, so the indicator slot is out — pandas slice would misalign on duplicate dates, polars eval rejects the length. A transform changes the x-domain itself, so it belongs *before* the view, at the same layer where a user resamples daily→weekly.

Key insight: mplchart's default rownum x-axis means a transformed frame works as chart prices directly — one brick per slot, dateaxis labels rows with their (non-uniform, possibly duplicated) completion dates. Same mechanism that hides weekend gaps; same rendering mplfinance produces for `type='renko'`.

Composability payoff: since the transformed output is an ordinary OHLCV frame, everything downstream composes for free — `SMA(20)` computes over brick closes (how renko traders actually use MAs), `Volume()` shows per-brick aggregated volume, panes and styles work untouched. mplfinance hardcodes `mav=` for renko and its pnf is currently broken against pandas 3.x (`_calculate_atr` does positional lookups on a DatetimeIndex series) — welding the transform into the plot pipeline is the fragile alternative we avoid.

## Phase 1 — `Chart(transform=...)`

Chart applies the transform to prices first thing, before creating the view:

```python
Chart(prices, transform=calc_renko).plot(Renko())
```

Implementation: in `init_prices`, after `normalize`, before `check_prices`/`get_view`. Transform spec is a plain callable `prices → frame` for now; a string registry (`transform="renko"`) needs a way to carry params (brick_size) and argues for transform objects — later, not now.

## Phase 2 — deferred view, transform at first use

**Wired in src (2026-07-25)** — `Chart.get_view(transform=None)` with `view` as a property, `config_date_axis` inside the creation path, late-transform and raw_dates guards raising, `check_prices` re-run on transform output. Tests in `tests/test_chart_view.py` (backend-parametrized). Original sketch:

Store prices at chart level; the view is created lazily by an accessor, and only the *first* access may pass a transform:

```python
@property
def view(self):
    return self.get_view()

def get_view(self, transform=None):
    if self._view is None:
        prices = transform(self._prices) if transform else self._prices
        self._view = get_view(prices, raw_dates=..., start=..., end=..., max_bars=...)
        if not self._view.raw_dates:
            config_date_axis(self.canvas.root_axes(), self._view.dates)
    elif transform is not None:
        raise ValueError("view already created — transform only at first use")
    return self._view
```

Payoff: the primitive carries the transform. `Renko(brick_size=2)` calls `chart.get_view(transform=...)` as its first act — `Chart(prices).plot(Renko(brick_size=2))`, no Chart-level param.

### Code findings (why this is safe)

Verified 2026-07-25: the view has exactly one pre-plot consumer — `config_date_axis(self.canvas.root_axes(), self.view.dates)` in `init_prices` (chart.py). It consumes only `view.dates` and is really "install the axis machinery once the view exists" — it moves inside the lazy creation path. Every other consumer is a primitive's `apply_to_chart` during `plot()` (14 files under `primitives/`), plus public `chart.view` reads, which the property preserves. Canvas, layout, and dateaxis modules are view-free.

## Decisions

- Windowing applies *after* the transform: `max_bars=100` means 100 bricks, not 100 days. Intentional.
- `raw_dates=True` + transform **raises** (decided 2026-07-25) — renko breaks hard (the +1ns nudge makes `nanmin(diff)` spacing collapse body widths to zero; without it same-day bricks stack), PnF loses its equal-width column grid. The guard lives where the transform is declared: `Chart(transform=)` at init (phase 1), `get_view(transform=)` (phase 2). A raw pre-plumbed `Chart(calc_renko(prices), raw_dates=True)` is unguardable and stays caveat-emptor.
- Transform spec: callable now; registry/objects when calc_renko params make it worth it.

## Caveats

- `chart.vline()` before `plot()` triggers view creation transform-less (VLine calls `map_date`) — the transform-bearing primitive must be the first view-toucher; the late-transform ValueError makes this loud.
- Duplicate completion dates (multi-brick days) **confirmed broken on pandas** (renko-proto, 2026-07-25): `PandasDataView.slice` aligned the windowed xloc against the full frame by date, and the inner join went cartesian on duplicate labels — rows multiplied and duplicate x-values collapsed the candle body width to zero via `nanmin(diff)`. Polars was positional and unaffected. **Fixed 2026-07-26**: the pandas slice is now positional outright (polars is the base model — dates are labels, not join keys; the date-join round-trip was only ever the identity under unique dates). The +1ns prototype nudge was removed from `calc_renko`; regression test in `test_renko.py::test_duplicate_dates_windowed_render`.
- `calc_renko` output: one row per brick — completion date, `open`/`close` = brick bottom/top (directional), `high`/`low` equal to them, volume summed since previous brick. numpy loop + `wrap_result`, both backends, same shape as `calc_heikin_ashi`.
- Brick size: fixed value param, ATR-ish default when unset.

## PnF outlook

Same mapping, one step further: `calc_pnf` emits one row per column (top/bottom/direction/date); the transform-then-render split carries over unchanged, but rendering needs a genuinely new primitive (X/O glyphs on a box grid) — no Candlesticks reuse.

Prototyped (2026-07-25) in `playground/pnf-proto.ipynb`: close-based 3-box reversal, `PointFigure` primitive (X = diagonal segment pairs via LineCollection, O = EllipseCollection with `units="xy"`), direction encoded intrabar (X column = up row) so the column frame is ordinary prices. Column start dates are strictly increasing — no timestamp nudge needed, unlike renko. Open items in its Findings cell: high/low-based extension (`method=`), percentage box sizes for long histories (a fixed box makes the first columns absorb years of range and volume), box-size metadata instead of grid inference.

## Next steps

- ~~Prototype `calc_renko` + rendering~~ — done (2026-07-25): `playground/renko-proto.ipynb` validates the whole mapping with zero Chart changes (both backends, composability with SMA/Volume, brick-space windowing). See its Findings cell.
- ~~Promote~~ — done (2026-07-25): `primitives/renko.py` (`calc_renko` + `Renko`) and `primitives/pointfigure.py` (`calc_pnf` + `PointFigure`), both binding their transform via `chart.get_view(transform=self.transform)` (bound method); `wrap_result(dates=...)` + `get_dates` in utils; tests in `tests/test_renko.py` / `tests/test_pointfigure.py` (backend-parametrized, hand-crafted sequences). The +1ns nudge shipped initially and was retired 2026-07-26 when the pandas slice went positional (see Caveats).
- Phase 1 (`Chart(transform=...)`) was skipped — the primitive-bound flow made it unnecessary.
- Open items: percentage (log) boxes for pnf/renko over long histories; high/low-based pnf (`method=`); configurable renko `reversal=`; proto notebooks still define local copies of the calcs — could be slimmed to import from src.
