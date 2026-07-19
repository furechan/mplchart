# Primitive ↔ Chart Contract

Living document: the full API surface primitives may use on the `Chart` object. Update whenever a primitive starts (or stops) using a `Chart` member. Any alternate core (see [polars-proposal.md](polars-proposal.md)) must implement the data plane below for existing primitives to run unchanged.

Last audited: 2026-07-18 (after hoisting `series_xy` onto `Chart`, narrowing `slice` to prices, and removing the `last_result` chaining cache — the data plane is now stateless).

## Rules

- Primitives never touch `chart.mapper` — the mapper is an implementation detail behind the data-plane methods.
- Primitives interact with data only through the data plane, and with matplotlib axes/colors only through the figure plane.
- Docstring examples may show the fluent API (`chart.plot`, `chart.pane`, `chart.hline`, `chart.vline`); those are not runtime dependencies of the primitives.

## Data plane

Methods that touch the data model. This is the entire surface to reimplement when swapping the core.

| Member | Call sites | Contract |
|---|---|---|
| `chart.series_xy(*values)` | 13 | Variadic: the window is computed once and applied positionally to every argument, which must be a full-length series/array aligned with prices. Returns `(x, *windowed_values)` numpy arrays — one shared x for all values. Single-series is the common form (`xv, yv = series_xy(y)`); Markers passes two (`xs, flag, close = series_xy(flag, close)`) to guarantee consistent windowing of co-dependent arrays. Alignment is positional, not index-based. Arguments may be numpy arrays, pandas Series, or polars Series — anything `np.asarray` accepts; a pandas index is discarded, never aligned on. Returns are always numpy. |
| `chart.prices` | 7 | Full-length unsliced prices frame. |
| `chart.calc_result(indicator)` | 7 | **Pure function** — evaluate indicator/expression → full-length **native** result: polars Expr → polars Series (struct → unnested polars DataFrame); tuple of Expr → polars DataFrame; pandas Expression → pandas Series; callable → whatever it returns (unchecked); `None` → `prices`. No normalization — consumers duck-type via `hasattr(data, "columns")`. No state: the `last_result` adjacency-chaining cache was removed 2026-07-18 — binding is explicit (constructor or `@`). |
| `chart.slice(data, xcol=None)` | 6 | **Domain: `chart.prices` only** — every call site passes the prices frame; windowing never applies to computed results (Peaks was the last exception, refactored 2026-07-18). Restrict prices to the visible window; returns the same backend as the input with an extra `xcol` column carrying per-row x-coordinates. `xcol` dtype depends on the mode: integer rownums (default) or datetime64 (`raw_dates`). Backend asymmetry: the polars path is strictly positional (assumes full-length data); the pandas default path aligns by datetime (inner join, tolerates partial data) and also re-indexes the result to the x-coordinates. |
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

### 5. Dual-mode study (Peaks)

A pattern of its own: two explicit modes decided by the constructor (`self.indicator is None`), each falling back to one of the base sequences — pattern 4's for prices, pattern 1's for a computed series:

- **OHLC mode** (`indicator=None`): `slice(chart.prices, xcol="xloc")` → peak kernel on `high` / valley kernel on `low` → sparse indices into `xloc`. Pattern 4's sequence feeding a geometry kernel; `calc_result` is never called.
- **Series mode** (bound indicator, constructor or `@`): `calc_result(ind)` → `series_xy(result)` → both peaks and valleys on the same values → sparse sub-selection of the windowed arrays. Pattern 1's sequence feeding a geometry kernel. The result must be a single series (explicit `ValueError` otherwise — compose a single-output expression).

Contrast with AutoPlot: there, multi-output means "draw more traces"; here the mode changes the *meaning* of the study (high/low vs same-series). This is the template for any future indicator + structure-study primitive.

### 6. Point lookup

- **VLine**: `map_date(date)` → single x-coordinate.

### 7. No data plane

- **HLine, Pane**: axes-only (`get_axes`); never touch data.

### Compute/window ordering

The patterns differ in *when* computation happens relative to windowing, and the difference is semantic, not stylistic:

- **Analytics compute full-length, then window** (the `calc_result` of patterns 1, 2 and 5): indicators need the full history for warmup (an EMA's value inside the window depends on data before it). Windowing first would change the numbers.
- **Geometry computes on the window** (the kernels of patterns 4 and 5: ZigZag, Peaks): structure studies are relative to what is visible — a pivot near the window edge depends on the window itself. Full-length computation then windowing would show dangling or missing segments.

Pattern 5 (Peaks, series mode) composes both rules in one primitive: full-length analytics feeding an in-window geometry kernel.

Any future core must preserve both orderings: window-at-extraction for expressions, window-before-kernel for structure primitives.

## Figure plane

Matplotlib-side surface — unaffected by any data-core swap.

| Member | Call sites | Contract |
|---|---|---|
| `chart.get_axes(target=None)` | 13 | Current or target pane axes. |
| `chart.get_color(name, ax, fallback=)` | 4 | Color resolution/cycling per axes: color_scheme lookup (raw name, then prefix), list cycling, `~` closest-color, `line`/`fill` dynamic fallback. The former `indicator` parameter was dead (rich-indicator era vestige) and removed 2026-07-18. |
| `chart.root_axes()` | 2 | Root (background) axes. |
| `chart.main_axes()` | 1 | Main price axes. |

## How to re-audit

```bash
grep -rn "chart\.[a-z_]*" src/mplchart/primitives/*.py src/mplchart/model/primitive.py -o \
  | awk -F: '{print $NF}' | sort | uniq -c | sort -rn
```

Exclude docstring-only hits (fluent-API examples) before updating the tables.
