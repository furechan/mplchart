# Primitive ↔ Chart Contract

Living document: the full API surface primitives may use on the `Chart` object. Update whenever a primitive starts (or stops) using a `Chart` member. Any alternate core (see [polars-proposal.md](polars-proposal.md)) must implement the data plane below for existing primitives to run unchanged.

Last audited: 2026-07-19 (after the backend-native mapper refactor: `DateMapper` contract + `PandasDateMapper`/`PolarsDateMapper` via `get_mapper`; legacy mappers removed).

## Rules

- Primitives never touch `chart.mapper` — the mapper (a backend-native `DateMapper`) is an implementation detail behind the data-plane methods.
- Primitives interact with data only through the data plane, and with matplotlib axes/colors only through the figure plane.
- Docstring examples may show the fluent API (`chart.plot`, `chart.pane`, `chart.hline`, `chart.vline`); those are not runtime dependencies of the primitives.

## Data plane

Methods that touch the data model. This is the entire surface to reimplement when swapping the core.

| Member | Call sites | Contract |
|---|---|---|
| `chart.series_xy(*series)` | 12 | Variadic: the window is computed once and applied positionally to every argument, which must be a full-length series/array aligned with prices. Returns `(x, *windowed_values)` numpy arrays — one shared x for all values. Single-series is the common form (`xv, yv = series_xy(y)`); Markers passes two (`xs, flag, close = series_xy(flag, close)`) to guarantee consistent windowing of co-dependent arrays. Alignment is positional, not index-based. Arguments may be numpy arrays, pandas Series, or polars Series; a pandas index is discarded, never aligned on. The full-length assumption is **enforced** — a length mismatch raises `ValueError` instead of silently clamping. Windowing is native per backend (polars Series are sliced natively, everything else through `np.asarray`); returns are always numpy. |
| `chart.prices` | 6 | Full-length unsliced prices frame (native backend, as supplied). |
| `chart.calc_result(indicator)` | 7 | **Pure function** — evaluate indicator/expression → full-length **native** result: str → native Series via plain column access (`prices[name]`); polars Expr → polars Series (struct → unnested polars DataFrame); tuple of Expr → polars DataFrame; pandas Expression → pandas Series; callable → whatever it returns (unchecked); `None` → `prices`. No normalization — consumers duck-type via `hasattr(data, "columns")`. No state: the `last_result` adjacency-chaining cache was removed 2026-07-18 — binding is explicit (constructor or `@`). |
| `chart.slice(data, xcol=None)` | 5 | **Domain: `chart.prices` only** — every runtime call is literally `chart.slice(chart.prices, xcol="xloc")`. Windows the prices frame; returns the same backend with an extra `xcol` column of per-row x-coordinates. `xcol` dtype depends on the mode: integer rownums (default) or datetime64 (`raw_dates`). Backend asymmetry: `PolarsDateMapper` slices positionally (assumes full-length, prices row order); `PandasDateMapper` joins on its stored date-indexed `xloc` series (inner join, tolerates partial data) and re-indexes the result to the x-coordinates. |
| `chart.map_date(date)` | 1 | Map a date to its x-coordinate (inverse lookup). Used by `vline`. |

Windowing responsibility is split: `calc_result` returns full-length data and `series_xy` does the windowing; the OHLC-family primitives window via `slice(xcol=...)` instead. Both converge on "filter to the x window" in a frame-based core.

## Data-bearing patterns

Every primitive follows one of the call sequences below. A recurring axis in the story is **output arity**: an indicator/expression yields either a single series or a multi-column frame (struct), and each pattern states how its primitives respond to that difference.

### 1. Compute → window (`calc_result` + `series_xy`)

Full-length series computed first, windowed at extraction. The default for anything that plots a computed series.

- **LinePlot, BarPlot, AreaPlot, Stripes**: `calc_result(ind)` → `series_xy(result)` → draw. Single-output only. An indicator is **required** (`required_indicator()` raises otherwise) — bare instances were only meaningful under the removed chaining cache.
- **AutoPlot**: same sequence, arity-aware rendering — single output → one trace; multiple outputs → one `series_xy(data[col])` per column, with naming conventions (`*hist` → bars, `upperband`/`middleband`/`lowerband` → band fill) deciding the mark. Arity changes *how much* is drawn, never the meaning.

### 2. Signal + price column (Markers)

`calc_result` for the analytics, a `chart.prices` column for placement — two already-aligned full-length arrays (both in prices row order by construction), windowed together by the variadic `series_xy`. No join or alignment happens; the variadic call only guarantees both are cut by the same window slice:

- **Markers**: `calc_result(ind)` → derive the signal flag; `chart.prices["close"]` → y-placement; `series_xy(flag, close)` applies one window slice to both against one shared x. The only variadic `series_xy` call site — used because the two arrays come from different sources, so neither frame idiom (`slice(xcol=...)`) applies.
- Distinct from pattern 1 in that the drawn y-values are *not* the computed result: the indicator only decides *where* markers go; prices decide *at what height*.

### 3. Self-computed price series (Price)

Pattern 1's shape, self-sourced: computes a price-derived series from `chart.prices` via its own `__call__` (`calc_price(prices, item)`), then `series_xy(series)` → draw.

- The `__call__` doubles as a plain callable indicator, so `Price("close")` also works anywhere a callable indicator is accepted (`LinePlot(Price("open"))`, `prices.pipe(...)`).
- Kin to pattern 4 in spirit (renders the price frame) but series-shaped in mechanics.

### 4. Window prices → read columns (`slice(chart.prices, xcol=...)`)

Raw prices windowed first with x materialized as the `xloc` column; values read per column. The idiom for primitives that render the price frame itself.

- **Candlesticks, OHLC, Volume**: `slice(chart.prices, xcol="xloc")` → read `xloc` + price columns → draw.
- **ZigZag**: same, then runs its kernel *on the windowed frame*; sparse indices map into `xloc`.

### 4. Dual-mode study (Swings)

A pattern of its own: two explicit modes decided by the constructor (`self.indicator is None`), each falling back to one of the base sequences — pattern 4's for prices, pattern 1's for a computed series:

- **OHLC mode** (`indicator=None`): `slice(chart.prices, xcol="xloc")` → peak kernel on `high` / valley kernel on `low` → sparse indices into `xloc`. Pattern 3's sequence feeding a geometry kernel; `calc_result` is never called.
- **Series mode** (bound indicator, constructor or `@`): `calc_result(ind)` → `series_xy(result)` → both peaks and valleys on the same values → sparse sub-selection of the windowed arrays. Pattern 1's sequence feeding a geometry kernel. The result must be a single series (explicit `ValueError` otherwise — compose a single-output expression).

Contrast with AutoPlot: there, multi-output means "draw more traces"; here the mode changes the *meaning* of the study (high/low vs same-series). This is the template for any future indicator + structure-study primitive.

### 5. Point lookup

- **VLine**: `map_date(date)` → single x-coordinate.

### 6. No data plane

- **HLine, Pane**: axes-only (`get_axes`); never touch data.

### Compute/window ordering

The patterns differ in *when* computation happens relative to windowing, and the difference is semantic, not stylistic:

- **Analytics compute full-length, then window** (the `calc_result` of patterns 1, 2 and 4): indicators need the full history for warmup (an EMA's value inside the window depends on data before it). Windowing first would change the numbers.
- **Geometry computes on the window** (the kernels of patterns 3 and 4: ZigZag, Swings): structure studies are relative to what is visible — a pivot near the window edge depends on the window itself. Full-length computation then windowing would show dangling or missing segments.

Pattern 4 (Swings, series mode) composes both rules in one primitive: full-length analytics feeding an in-window geometry kernel.

Any future core must preserve both orderings: window-at-extraction for expressions, window-before-kernel for structure primitives.

## Figure plane

Matplotlib-side surface — unaffected by any data-core swap.

| Member | Call sites | Contract |
|---|---|---|
| `chart.get_axes(target=None)` | 12 | Current or target pane axes. |
| `chart.get_color(name, ax, fallback=)` | 4 | Color resolution/cycling per axes: color_scheme lookup (raw name, then prefix), list cycling, `~` closest-color, `line`/`fill` dynamic fallback. The former `indicator` parameter was dead (rich-indicator era vestige) and removed 2026-07-18. |
| `chart.root_axes()` | 2 | Root (background) axes. |
| `chart.main_axes()` | 1 | Main price axes. |

## Findings

Empirical remarks from the audits — properties the call sites exhibit that the signatures don't require. Each is a simplification opportunity or an invariant worth defending.

- **`slice` has no free parameters in practice.** All 5 runtime calls are character-for-character `chart.slice(chart.prices, xcol="xloc")` — `data` is always prices, `xcol` always `"xloc"`. A no-argument windowed-prices accessor (e.g. `chart.window()`) would express what every caller means; `slice`'s signature is vestigial.
- **`calc_result` always flows into `series_xy`, and nothing in between changes row count or order.** The only in-between steps are column selection (per-column `_series` in AutoPlot) and pointwise transforms (Markers' `clip(sign(...))`) — never a filter, sort, dropna, or resample. This row-preservation is what makes positional `series_xy` safe; the length half is now enforced at the boundary (`ValueError` on mismatch), while row *order* remains upheld by convention. Side note: `item=` has been dropped from LinePlot/BarPlot/AreaPlot too (2026-07-19) — selection is by composition (`.struct.field(...)` / `as_expr(item=...)`), same message as Swings. A plain string is now a first-class indicator form meaning **column reference only**: `apply_indicator` resolves it as native column access (`prices[name]` — `pl.col` semantics, no derived-price aliases; typical price is `TYPPRICE()`), `is_indicator_like` accepts it, and `get_label` returns it verbatim — so `LinePlot("close")`, `chart.plot("close")`, and `"close" @ LinePlot()` all work. This is the IntoExpr contract at the evaluation layer, where it belongs.
- **Computed results never re-enter a frame.** Results live as Series/arrays outside prices from `calc_result` to `series_xy`. The one primitive needing a computed value *alongside* a prices column (Markers) is exactly why the variadic `series_xy` exists — in a frame model (`with_columns`) that need, and the variadic form, disappear.
- **`series_xy` is single-series at 12 of 13 sites.** Markers is the only variadic caller (two sources, no common frame — see above).
- **Two disjoint data idioms, split by data shape.** Frame-shaped primitives use `slice` + column reads; series-shaped primitives use `calc_result` + `series_xy`. No primitive mixes idioms except Swings, which dispatches between them by constructor mode.
- **`get_color` is AutoPlot-only.** Explicit primitives resolve colors themselves (`self.color or rcParams`); the color_scheme applies only to auto-plotted traces. Whether that asymmetry is intended is worth an explicit decision.
- **`map_date` has exactly one consumer** (VLine). The inverse date→x mapping is nearly unused surface.
- **`indicator=None` is meaningful only for Swings** (OHLC mode); every other binding primitive requires an indicator. The None-case is per-primitive semantics, not a data-plane concept.
- **The `Price` primitive is retired (2026-07-19).** Its accessor role is played by the bare column string (`LinePlot("close")`), its derived prices by named indicators (`MEDPRICE`/`TYPPRICE`/`WCLPRICE`/`AVGPRICE`, talib naming). The last primitive-moonlighting-as-indicator dual role is gone.
- **`chart.prices` is one refactor away from leaving the surface.** Six runtime accesses: five are the uniform `chart.slice(chart.prices, xcol="xloc")` idiom (a no-arg windowed-prices accessor would absorb them), and one is Markers reading the close column directly — replaceable by `calc_result("close")` now that strings are indicators. Both done, the data plane shrinks to four members (`window`, `calc_result`, `series_xy`, `map_date`) and primitives never see the raw frame — freeing the future core to restructure it (x/width columns, projections) without any primitive depending on its shape.
- **The contract has survived one core swap already.** The backend-native mapper refactor (2026-07-19) replaced the entire windowing implementation with zero primitive changes — empirical validation of the contract as the transition mechanism for the polars migration.

## How to re-audit

```bash
grep -rn "chart\.[a-z_]*" src/mplchart/primitives/*.py src/mplchart/model/primitive.py -o \
  | awk -F: '{print $NF}' | sort | uniq -c | sort -rn
```

Exclude docstring-only hits (fluent-API examples) before updating the tables.
