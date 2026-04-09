---
name: Polars migration plan
description: Plan to migrate mplchart from pandas-only to pandas+polars with expression support in the plot API
type: project
---

Migration plan documented in `docs/migration-breakdown.md` (per-file) and `docs/migration-inquiry.md` (phase-based overview).

**Why:** Support polars DataFrames natively and allow `pl.Expr` objects as column selectors / indicators in `chart.plot()`.

**Key architectural decisions:**
- Keep pandas DatetimeIndex as-is (no reset_index); extract datetime as numpy array once in `init_mapper` via `extract_datetime(df)` — pandas uses `df.index.values`, polars uses `df["datetime"].to_numpy()`
- `rownum = np.arange(len(prices))` — integer row numbers used as matplotlib x-coordinates; gap removal (weekends/holidays) is a free consequence
- `window = slice(start_row, end_row)` — `np.searchsorted` on datetime array; works uniformly on numpy, pandas Series, polars Series
- `mapper.series_xy(values, window)` → `(rownum[window], values[window])` — pure numpy, universal
- Indicators must return same-length output (NaN-padded); irregular primitives (zigzag, peaks, stripes, markers) own their x/y extraction using `rownum[their_row_indices]`
- No `library_polars.py` — polars computation lives in the new `expressions/` subpackage
- Multi-column expressions return **tuple of `pl.Expr`**, not `pl.struct`
- `expressions/` subpackage follows bearta conventions: `wrap_expression` decorator, uppercase factory names (SMA, EMA, etc.), `src=CLOSE` keyword default

**How to apply:** When implementing any part of this migration, refer to the breakdown doc for before/after code. Start with mapper rewrite (Phase 3) as it unblocks everything else.
