# Canvas / View — Roadmap

Evolution plan (2026-07-19) for moving from today's code to the [target API](canvas-view-sketch.md). Rationale in [canvas-view-rationale.md](canvas-view-rationale.md). Phases land in order; every step ends with `uv run pytest` green, and each phase with `inv check` (lint + nbcheck examples). Steps within a phase are individually committable.

## Phase 1 — dateaxis + DataView

The data plane, extracted and promoted. After this phase the no-Chart native-plotting playground works.

1. **Extract dateaxis**: new `dateaxis.py` consolidating `locators.py` + `formatters.py`; add `config_date_axis(ax, dates)`. Old modules become re-export shims (or update imports and drop them).
2. **Make the mapper matplotlib-free**: move `DateMapper.config_axes` wiring out — the native `dates` attribute (already public) is the contract, declared on the ABC; `_dt_array` removed, since dateaxis coerces native dates to numpy at its own boundary. `Chart.init_prices` calls `config_date_axis(root, mapper.dates)` when not `raw_dates`. Mapper no longer imports dateaxis.
3. **Rename mapper → DataView**: `mapper.py` → `dataview.py`; `DateMapper` → `DataView`, `PandasDateMapper` → `PandasDataView`, `PolarsDateMapper` → `PolarsDataView`, `get_mapper` → `get_view` (removed outright — no alias); `chart.mapper` → `chart.view` (deprecated property alias).
4. **Move evaluation in**: each subclass implements `eval` in full (no shared template) — `PandasDataView`: str, pandas Expression (`_eval_expression` hook), callable; `PolarsDataView`: str, `pl.Expr`/tuple (struct unnest), callable. Implementation moves from `utils.apply_indicator`, which stays self-contained but deprecated (it accepts any frame; `prices.pipe(...)`-style helpers and tests may use it).
5. **Fused forms**: `series_xy` accepts item-likes (eval'd full-length, then windowed together); `window(item=None)` — rename/absorb `slice`, materializing `xloc` by default. `chart.slice` retained as deprecated alias.
6. **Repoint primitives** (done 2026-07-19, ahead of step 5): all data-plane calls go through `chart.view.*` (`eval`, `series_xy`, `slice`, `map_date`, `prices`); Chart's wrappers (`slice`, `series_xy`, `map_date`, `calc_result`) removed outright — no notebook or test used them. Pattern-1 primitives keep the two-step `eval` + `series_xy` until step 5's fused forms.
7. **Docs**: re-audit [primitive-contract.md](primitive-contract.md) (data-plane table now points at DataView); update [architecture.md](architecture.md) module table.

## Phase 2 — Canvas

The presentation plane, built green-field under Chart.

1. **New `canvas.py`** (drafted 2026-07-19, standalone): `Canvas` class — figure creation (tight layout, figsize, adopt-and-clear existing figure), styled root + panes (`config_root_axes`/`config_pane_axes`), `get_axes` targets, `count_axes`, and the color machinery (`get_color`, scheme, cycling). Geometry stays shared via `layout.py`; Chart still carries its own copies of styling/pane/color logic until step 2.4 hooks it in.
2. **Chart delegates**: `chart.canvas` created in `__init__`; the old Chart methods become deprecated aliases; primitives switch figure-plane calls to `chart.canvas.*`. `layout.py` retired or reduced to internals.

## Phase 3 — Contract restated

1. Restructure [primitive-contract.md](primitive-contract.md) around the DataView and Canvas interfaces; new rule: a primitive may touch `chart.view` and `chart.canvas` and nothing else on the chart.
2. Verify by audit (the grep in that doc): no primitive touches any other `chart.*` member.

## Phase 4 — Signature flip

1. `Primitive.apply(canvas, view)` becomes the contract; `apply_to_chart(chart)` becomes the shim (`self.apply(chart.canvas, chart.view)`), deprecated. `Chart.plot_indicator` dispatch updated to the new hook.
2. Playground notebook exercising primitives Chart-less (`Candlesticks().apply(canvas, view)`), doubling as the contract's proof.
3. Optional stop: phase 3 already delivers the contract in substance; flip only if the two-namespace form chafes.

## Deprecations ledger

| Alias | Introduced | Replaces |
|---|---|---|
| `chart.mapper` | phase 1.3 | `chart.view` |
| `apply_indicator` | phase 1.4 | `DataView.eval` |
| `apply_to_chart` | phase 4.1 | `apply(canvas, view)` |

Remove together in a major-ish cleanup release once notebooks and README no longer reference them.
