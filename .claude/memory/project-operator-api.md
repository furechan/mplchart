---
name: New indicator/expression operator API
description: Resolved operator design — | for indicators, @ for expressions→primitives, .apply() replaces deprecated @
type: project
---

mplchart is the testbed for a new unified operator API to be applied to mintalib, barcalc, finchart.

**Rule: `|` is for the indicator world. `@` is for the expression world.**

| Expression | Meaning |
|---|---|
| `prices \| SMA(50)` | eager apply — left-to-right pipeline |
| `SMA(50) \| ROC(1)` | chain indicators |
| `SMA(50) \| LinePlot()` | indicator → primitive |
| `pl_expr @ LinePlot()` | expression → primitive (polars only) |
| `SMA(50).apply(prices)` | explicit apply (replaces deprecated `@`) |
| `SMA(20).apply(EMA(10))` | explicit compose (replaces deprecated `@`) |

**Why:** `pl.Expr` owns `|`, `>>`, and arithmetic operators. `@` (`__matmul__`) is the only operator polars does not define — so `pl_expr @ Primitive` falls through to `Primitive.__rmatmul__` cleanly.

**Implementation in model.py:**
- `Indicator.__pandas_priority__ = 5000` — preempts `DataFrame.__or__`, enables `prices | SMA(50)`
- `Indicator.__ror__` — applies indicator when data is on the left
- `Indicator.apply(other)` — apply to data or compose with another indicator
- `Indicator.__matmul__` — returns NotImplemented for Primitive; warns for compose/apply
- `Primitive.__rmatmul__` — accepts pl.Expr or callable; warns if Indicator (use | instead)

**Why:** Indicators are legacy (pandas); expressions are the polars-native future. Giving each world its own operator keeps the API clean and sets direction for the migration.
