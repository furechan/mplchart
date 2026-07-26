---
name: project-operator-api
description: Constructor form is the primary binding style; @ is the operator alternative; | chains indicators
metadata:
  type: project
---

Binding an indicator/expression to a primitive has two equivalent forms. Since 2026-07 the **constructor form is the primary documented style** (README, notebooks, docstrings); `@` remains fully supported as the operator form:

| Expression | Meaning |
|---|---|
| `LinePlot(SMA(50), color="red")` | bind indicator to a primitive (primary form) |
| `SMA(50) @ LinePlot(color="red")` | same — operator form |
| `pl_expr @ Stripes()` | bind polars Expr to a primitive (works — pl.Expr has no `__matmul__`) |
| `pd_expr @ Stripes()` | **broken** — pandas Expression swallows `@` silently; use `Stripes(pd_expr)` (see [[project-pandas-expressions-gotchas]]) |
| `SMA(50) | EMA(20)` | chain indicators left-to-right (`IndicatorChain`) |
| `indicator | primitive` | deprecated binding — warns, directs to constructor/`@` |
| `prices.pipe(SMA(50))` or `SMA(50)(prices)` | apply indicator to data (`prices | indicator` was removed in 0.0.36 along with `__pandas_priority__`) |

**Why constructor-first:** immune to the pandas-Expression `@` trap, no precedence parens (`(expr < 30) @ Stripes()` vs `Stripes(expr < 30)`), discoverable via signature help, and finchart has no binding operator at all (constructor-only).

**Why `@` for the operator:** `pl.Expr` owns `|` and arithmetic; `@` is the operator polars does not define, so `pl_expr @ Primitive` falls through to `Primitive.__rmatmul__` cleanly.

**Implementation in `model/primitive.py`:**
- `BindingPrimitive` — base for `LinePlot`, `AreaPlot`, `BarPlot`, `Stripes`, `Markers`, `Peaks`; holds `indicator` as first positional arg, `__rmatmul__` (accepts any `is_indicator_like`; clones with indicator bound), and deprecated `__ror__`.
- `AutoPlot` is the exception: its constructor takes only `label`, so `@` (or `clone(indicator=...)`) is the only binding path there.

**`Stripes`/`Markers` pattern:** compose the condition first — `Stripes(RSI().as_expr() < 30)` (pandas) or `Stripes(RSI() < 30)` (polars expressions).

**Open design question (cross-project):** `|` for indicator chaining (`DEMA(20) | ROC(1)`) operates at the concrete/data level, while polars pipes compose at the expression level — a known semantic mismatch. Decision deferred to mintalib, where the same indicator/expression duality exists; any change must be consistent across both libraries. Status: `|` chaining is acceptable-as-is until the mintalib direction is decided.
