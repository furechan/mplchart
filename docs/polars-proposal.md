# Polars Proposal

> **Status: discussion document.** This captures a design conversation (July 2026) exploring a polars-only future for mplchart. Nothing here is decided, designed in detail, or scheduled for implementation.

## Background

The pandas/polars-agnostic conversion left the library carrying two parallel analytics paths: pandas indicator classes (`indicators.py`, `library.py`, `model/indicator.py`) and polars expression factories (`expressions/`), with full 1:1 parity across all 30 indicators. The agnostic core is held together by backend detection and numpy as the lowest common denominator (`utils.py`). This ambivalence is costly: every indicator exists twice, and the backend-neutral plumbing forces low-level numpy work that polars handles natively.

## Proposal in one sentence

A chart is a polars frame with an x column; expressions compute columns; primitives draw columns; the axis formats x back into labels.

## Core ideas

### 1. Polars-only analytics, pandas accepted at the door

The library would accept prices as pandas or polars, convert once at the `Chart` boundary (`normalize_prices` already handles the DatetimeIndex → date-column promotion), and assume polars everywhere downstream. Polars becomes a hard dependency; pandas is detected but never imported. The pandas indicator stack (~1,100 lines: `indicators.py`, `library.py`, `model/indicator.py`, `pandas.py`) is deleted, along with the backend-detection machinery and the pandas-expression gotchas (`__getattr__` trap, `callable` trap, `@`-binding shadowing).

Since expression factories match the indicator classes in name and signature, `mplchart.indicators` could re-export the expression factories for a release or two to keep old notebooks working.

### 2. Primitives take expressions (the IntoExpr contract)

Every data parameter of a primitive accepts `str | pl.Expr`, normalized via `pl.col()` — polars' own `IntoExpr` pattern. `LinePlot("close")`, `LinePlot(SMA(20))`, and `LinePlot(CLOSE.rolling_mean(20))` are the same call. `Candlesticks(open=..., high=..., low=..., close=...)` parameterized by expressions makes Heikin-Ashi, smoothed candles, or spread charts a *usage* rather than a feature.

The user-facing distinction between expression and primitive dissolves; internally the boundary stays crisp: expressions compute columns, primitives own axes and artists.

### 3. X as a column — the mapper collapses

The projection from rows to x-coordinates becomes data instead of coordinate machinery: an `x` column produced by an expression. Standard chart: `x = int_range(pl.len())` (rownum). Raw-date chart: `x = date`. PNF/renko: `x` is the column index emitted by the projection. Variable-width bars: `x` is a cumulative-width midpoint plus a `width` column.

Consequences:

- Slicing becomes a `filter` on the x range.
- Irregular primitives (ZigZag, Swings, Markers) stop indexing `mapper.rownum` by hand; sparse data with its own x travels naturally in a frame.
- Alignment is positional by construction — the index-alignment bug class disappears.
- The mapper's surviving job is the **inverse** mapping: tick locating and labeling. `DTArrayLocator`/`DTArrayFormatter` get demoted to a formatter backed by an `(x, label)` pair of columns doing nearest-row lookup. The existing numpy-level tick logic remains available as the fallback where polars offers no higher-level abstraction.

Invariants to keep in view: all panes share one x (`sharex`), so the x column is chart-owned — a projection like PNF defines the *chart's* frame, not one primitive's input. Unit-width assumptions in candlesticks/bars (`width=0.8` in rownum space) must become explicit: a constant per projection or a `width` column.

### 4. Numba kernels behind the expression facade

Polars expressions cannot express sequential state machines (row *i* depends on emitted state at row *i-1*): SAR, zigzag, KAMA, PNF/renko projections. bearta's `kernel_expression` pattern (pack input expressions into a struct → one `map_batches` crossing → `@njit` kernel → `pl.Expr`) hides such kernels behind the expression interface, so adopting numba adds no third paradigm.

Cautions: numba is the heaviest dependency in the stack (LLVM, import time, JIT warmup, version lag). Preferred shape: optional extra with a no-op `njit` fallback so the same kernel source runs as a plain Python loop (fine on daily data), lazy-imported to keep `import mplchart` fast.

### 5. Explicit styling over smart defaults

No per-indicator plotting registry or metadata magic. Users who care about overbought levels care about *which* levels, so explicit `LinePlot(RSI(14), overbought=70, oversold=30)` and `pane(yticks=...)` win over pre-filled defaults. The one convention layer kept is AutoPlot's output contract: struct field names (`*hist` → bars, `upperband`/`lowerband`/`middleband` → band fill) drive render style — the expression declares its shape, the plotter renders the shape.

## What mplchart is

The shape of the output decides what belongs in the package:

- **Column-shaped analytics** (SMA, RSI, MACD — one value per row) are expression territory. Bundled today as a facility; could be thinned or imported from bearta once it is public. Not mplchart's competitive surface — the layering across projects would be mintalib/bearta for TA, mplchart for charting.
- **Structure-shaped studies** (trendlines, zigzag, support/resistance zones, PNF columns — output is geometry: segments, pivots, boxes, levels) are mplchart's actual product. Their calculation is inseparable from chart context (visible window, pane, visual judgment) and cannot honestly be returned as a series. The rich-indicator paradigm (calculation + plotting fused in one object) survives here, in the primitive layer, where it is irreplaceable — with polars frames and numba kernels replacing raw numpy for the calculation half (geometry as a small frame of `(x0, y0, x1, y1)` rows).
- **The chart frame** — one polars DataFrame with an x column — mediates between the two.

## Transition mechanism

Follow-up analysis (see [primitive-contract.md](primitive-contract.md)) established that the primitive ↔ Chart interface is small enough to hold invariant across the core swap: five data-plane methods (`prices`, `calc_result`, `slice`, `series_xy`, `map_date`) and four figure-plane methods. All five data-plane methods have direct implementations on a polars frame carrying an x column; `series_xy` has been hoisted onto `Chart` and no primitive touches `chart.mapper` anymore. Existing primitives therefore run unchanged on a new core from day one; the mapper dissolves (projection → x column, windowing → filter, ticks → formatter over the `(x, date)` columns) rather than being ported. The intact interface is the transition mechanism, not the destination — primitives can then migrate to IntoExpr signatures incrementally.

Two deliberate contract narrowings: `calc_result` drops the pandas-expression branch and pandas-only callables (returns collapse to polars Series/DataFrame); `slice` becomes strictly positional everywhere, dropping the pandas path's datetime inner-join tolerance.

## Open questions

- Numeric parity check (EMA seeding, RMA warmup, NaN-vs-null edges) between pandas indicators and polars expressions before the pandas stack is deleted — the expressions must be the reference implementation, not an approximation.
- Contract for plain-callable custom indicators (would receive a polars DataFrame).
- Where chart-specific kernels live (zigzag, projections stay in mplchart; SAR/KAMA-class analytics do not) and whether mplchart depends on bearta, vendors kernels, or both.
- Whether `mplchart.indicators` re-exports expressions temporarily or is dropped outright.
- Timing relative to bearta being published.
