---
name: Indicator/expression operator API
description: Unified operator design — @ is the binding operator for both indicators and expressions
type: project
---

`@` is the single binding operator for both pandas indicators and polars expressions.
`|` for binding is deprecated (warns) but still works for backward compat.

| Expression | Meaning |
|---|---|
| `prices \| SMA(50)` | apply indicator to data |
| `SMA(50) \| EMA(20)` | chain indicators left-to-right |
| `SMA(50) \| (lambda s: s < 30)` | chain indicator with lambda (via `Indicator.__or__`) |
| `SMA(50) @ LinePlot(color="red")` | bind indicator to a primitive |
| `LinePlot(SMA(50), color="red")` | same — indicator as first positional arg |
| `RSI() @ Stripes()` | bind polars Expr or indicator to a primitive |

**Why `@`:** `pl.Expr` owns `|` — `@` (`__matmul__`) is the only operator polars does not define, so `expr @ Primitive` falls through to `Primitive.__rmatmul__` cleanly. Unifying on `@` removes the pandas-vs-polars syntax split.

**Implementation in model.py:**
- `Indicator.__pandas_priority__ = 5000` — preempts `DataFrame.__or__`, enables `prices | SMA(50)`
- `Indicator.__or__` — chains with any callable (including lambdas) via `IndicatorChain`
- `Indicator.__ror__` — chains with another Indicator or applies to data
- `BindingPrimitive.__rmatmul__` — accepts any indicator-like (pl.Expr, callable); clones with indicator bound
- `BindingPrimitive.__ror__` — deprecated binding via `|`; emits DeprecationWarning

**BindingPrimitive base class** (in `model.py`):
- All indicator-bindable primitives inherit from it: `LinePlot`, `AreaPlot`, `BarPlot`, `Stripes`, `Markers`, `Peaks`, `AutoPlot`
- Holds `indicator = None`, `__init__(self, indicator=None)`, `__rmatmul__`, `__ror__`
- `indicator` is first positional arg — `LinePlot(SMA(50), color="red")` works
- `Stripes` and `Markers` have no `expr` param — compose the condition before binding

**`Stripes` / `Markers` pattern:**
```python
(RSI() | (lambda s: s < 30)) @ Stripes(color="green")   # pandas
(RSI() < 30) @ Stripes(color="green")                    # polars
```
