# Backlog

Items decided or considered but not scheduled. Add new items at the end.

## API

- Consider a polars `merge_prices` equivalent to `mplchart.pandas.merge_prices` — would unblock a polars version of `compare-tickers.ipynb`

## Expression API

- Design decision: finalize the full set of expression forms accepted by `resolve_expr` (and by `expr=` on primitives like Stripes/Markers). Today we accept callables, `pl.Expr`, and strings — the strings' semantics diverge (pandas `df.eval` is lenient, polars SQL is strict). Decide: (a) keep all three; (b) tighten string semantics so both backends behave the same way (e.g. strict-missing-column on pandas too); (c) whether a pandas-side first-class expression type is worth introducing for symmetry with `pl.Expr`, or whether the callable form IS the pandas equivalent. Then document the chosen contract (return shape, valid input shapes, cross-backend guarantees) on `resolve_expr` and in the README.
- Support struct expressions as multi-output shape. Today multi-output is always tuple-of-Expr (ExprTuple). Some libraries (e.g. mintalib style) expose multi-output as a single `pl.Expr` that evaluates to a Struct series. `apply_indicator` / `get_label` / `AutoPlot` would need to detect struct-output exprs, unnest the result, and extract field names from the Struct dtype for legend/column keys.


