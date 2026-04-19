# Backlog

Items decided or considered but not scheduled. Add new items at the end.

## API

- Rename `AutoPlotter.series_xy` to `data_xy` or similar — differentiate from `utils.series_xy` (TODO in `plotters.py`)
- Consider a polars `merge_prices` equivalent to `mplchart.pandas.merge_prices` — would unblock a polars version of `compare-tickers.ipynb`

## Expression API

- Design decision: finalize the full set of expression forms accepted by `resolve_expr` (and by `expr=` on primitives like Stripes/Markers). Today we accept callables, `pl.Expr`, and strings — the strings' semantics diverge (pandas `df.eval` is lenient, polars SQL is strict). Decide: (a) keep all three; (b) tighten string semantics so both backends behave the same way (e.g. strict-missing-column on pandas too); (c) whether a pandas-side first-class expression type is worth introducing for symmetry with `pl.Expr`, or whether the callable form IS the pandas equivalent. Then document the chosen contract (return shape, valid input shapes, cross-backend guarantees) on `resolve_expr` and in the README.
- Support struct expressions as multi-output shape. Today multi-output is always tuple-of-Expr (ExprBundle). Some libraries (e.g. mintalib style) expose multi-output as a single `pl.Expr` that evaluates to a Struct series. `apply_indicator` / `get_label` / AutoPlotter would need to detect struct-output exprs, unnest the result, and extract field names from the Struct dtype for legend/column keys.

## Tests

- Expand `resolve_expr` coverage in Stripes/Markers tests. Currently only the Series+lambda path is exercised. Missing: string column-select on a DataFrame (e.g. `MACD() | Markers(expr="macdhist")`), lambda on a DataFrame (e.g. `Stripes(expr=lambda df: df["close"] < df["open"])`), and `pl.Expr` form on polars.

## Indicators

- Consider removing slow/complex indicators like SLOPE and CURVE — assess whether the complexity is worth keeping in the library.

## mintalib

Related — the tactical and strategic halves of the same question. Writing tests forces a catalog of what mplchart actually consumes from mintalib, which directly informs the source-of-truth decision.

- Review the indicators/expressions split across mplchart, mintalib/barcalc, and besrta — decide whether mintalib/barcalc becomes the source of truth for indicators and mplchart's `library.py` / `expressions/` subpackage get deprecated in favor of importing from there. (Integration tests landed — `test_mintalib_indicators.py` and `test_mintalib_expressions.py` — which will help inform this.)
