---
name: Indicator/expression operator API
description: Resolved operator design — | for indicators, @ for expressions→primitives
type: project
---

mplchart is the testbed for a unified operator API to be applied to mintalib, barcalc, finchart.

**Rule: `|` is for the indicator world. `@` is for the expression world.**

| Expression | Meaning |
|---|---|
| `prices \| SMA(50)` | apply indicator to data (left-to-right) |
| `SMA(50) \| ROC(1)` | chain indicators left-to-right |
| `SMA(50) \| LinePlot()` | bind indicator to a primitive |
| `pl_expr @ LinePlot()` | bind expression to a primitive (polars only) |

**Why:** `pl.Expr` owns `|`, `>>`, and arithmetic operators. `@` (`__matmul__`) is the only operator polars does not define — so `pl_expr @ Primitive` falls through to `Primitive.__rmatmul__` cleanly.

**Implementation in model.py:**
- `Indicator.__pandas_priority__ = 5000` — preempts `DataFrame.__or__`, enables `prices | SMA(50)`
- `Indicator.__ror__` — chains with another Indicator or applies to data
- `Primitive.__ror__` — defined per primitive (LinePlot, AreaPlot, etc.); clones with indicator bound
- `Primitive.__rmatmul__` — accepts pl.Expr or any callable; warns if Indicator (use `|` instead)

Note: `ComposedIndicator` and `Indicator.__matmul__` were removed. `IndicatorChain` (via `|`) is the only composition mechanism.
