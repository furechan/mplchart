---
name: Pandas expressions gotchas
description: Known pitfalls with pandas.api.typing.Expression (__getattr__ trap, callable trap, private eval hook)
type: project
---

`pandas.api.typing.Expression` (introduced in pandas 3.0 via `pd.col()`) has several design problems that make it hazardous to handle alongside normal Python objects.

## The `__getattr__` trap

`Expression` implements `__getattr__` to support method chaining (`pd.col("close").rolling(20).mean()`). Side effect: **`hasattr(expr, anything)` always returns `True`**, and `getattr(expr, "foo", default)` never falls back to `default` — it returns a new Expression instead.

This broke three places in mplchart before being caught:
- `hasattr(indicator, "plot_handler")` — silently routed expressions into a no-op path
- `hasattr(indicator, "func_object")` — fired the talib branch and crashed on iteration
- `getattr(indicator, "metadata", None)` — returned a truthy Expression, crashed on `.get()`

**Rule:** for capability checks use `hasattr(type(indicator), "method")`, never the instance. For data attributes (`label`, etc.), guard with `is_pandas_expr(indicator)` first.

## The `callable` trap

`callable(expr)` returns `True`, but calling `expr(df)` does NOT evaluate the expression — it returns a string representation applied to the DataFrame. The real evaluation hook is `expr._eval_expression(df)`, which returns a `pd.Series`.

## Private evaluation API

`_eval_expression` is underscore-prefixed — not a public API. It could change or get a public replacement as the expressions API matures (it is explicitly experimental in pandas 3.0).

**How to apply:** monitor pandas release notes for a stable public evaluation API to replace `_eval_expression`. When found, update `apply_indicator` and `resolve_expr` in `utils.py`.

## Detection

Both `is_polars_expr` and `is_pandas_expr` use class `__dict__` checks to bypass `__getattr__`:

```python
def is_polars_expr(item): return "_pyexpr" in type(item).__dict__
def is_pandas_expr(item): return "_eval_expression" in type(item).__dict__
```

`hasattr` on the instance is unreliable for pandas expressions. Always check `type(item).__dict__` or `type(item)`.
