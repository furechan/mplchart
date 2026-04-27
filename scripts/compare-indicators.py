"""Compare indicator names in mplchart.indicators vs mplchart.expressions."""

from mplchart.indicators import __all__ as _indicators
from mplchart.expressions import __all__ as _expressions

non_indicators = {"wrap_expression", "ExprTuple", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"}

indicators  = set(_indicators)
expressions = set(_expressions) - non_indicators

only_indicators = sorted(indicators - expressions)
only_expressions = sorted(expressions - indicators)
both = sorted(indicators & expressions)

print(f"In both ({len(both)}): {', '.join(both)}")
print()
if only_indicators:
    print(f"Indicators only — missing from expressions ({len(only_indicators)}): {', '.join(only_indicators)}")
else:
    print("Indicators only: none")
print()
if only_expressions:
    print(f"Expressions only — no indicator equivalent ({len(only_expressions)}): {', '.join(only_expressions)}")
else:
    print("Expressions only: none")
