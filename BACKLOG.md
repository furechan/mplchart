# Backlog

Items decided or considered but not scheduled. Add new items at the end.

## API

- Consider a polars `merge_prices` equivalent to `mplchart.pandas.merge_prices` — would unblock a polars version of `compare-tickers.ipynb`

## Expression API

- Support struct expressions as multi-output shape. Today multi-output is always tuple-of-Expr (ExprTuple). Some libraries (e.g. mintalib style) expose multi-output as a single `pl.Expr` that evaluates to a Struct series. `apply_indicator` / `get_label` / `AutoPlot` would need to detect struct-output exprs, unnest the result, and extract field names from the Struct dtype for legend/column keys.


