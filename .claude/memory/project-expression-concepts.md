---
name: project-expression-concepts
description: two expression systems — expressions are polars-native; pandas 3.0 "column expressions" are a lightweight adaptation, not a native feature; don't conflate
metadata:
  type: project
---

mplchart touches two distinct expression systems that must not be conflated:

- **Polars expressions** (`pl.Expr`) — expressions are a *native* polars concept: lazy, composable column computations, first-class in the polars API. `mplchart.expressions` builds on them and is polars-only ([[project-backend-architecture]]).
- **Pandas column expressions** (`pandas.api.typing.Expression`, via `pd.col()`, new and experimental in pandas 3.0) — a *lightweight adaptation* of the polars concept onto pandas, not really a native pandas feature. mplchart interops with them (indicators expose `.as_expr()` for boolean composition like `RSI(14).as_expr() > 30`; evaluation goes through the private `_eval_expression` hook); the handling pitfalls are in [[project-pandas-expressions-gotchas]].

So "pandas expressions" in this project always means the pandas 3.0 column-expression interop — never a pandas implementation of the `mplchart.expressions` module.

**Why:** a context quiz (2026-07-26) showed the memory index conveyed the gotchas but not the concept — an agent conflated pandas and polars expressions and flagged a false contradiction with the polars-only expressions module.
