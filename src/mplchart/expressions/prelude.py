"""Expression prelude — constants and wrap_expression decorator"""

import polars as pl
from functools import wraps


OPEN = pl.col("open")
"""Column expression for the ``open`` price."""

HIGH = pl.col("high")
"""Column expression for the ``high`` price."""

LOW = pl.col("low")
"""Column expression for the ``low`` price."""

CLOSE = pl.col("close")
"""Column expression for the ``close`` price. The default source of single-series factories."""

VOLUME = pl.col("volume")
"""Column expression for the ``volume`` series."""


def wrap_expression(func):
    """Decorator for expression factory functions.

    Allows the first positional argument to be a pl.Expr, which is then
    passed as the `src` keyword argument. This enables both calling styles:

        SMA(20, pl.col("close"))   # positional expr
        SMA(20)                    # defaults to CLOSE
        SMA(20, src=pl.col("open"))

    Aliases the resulting ``pl.Expr`` with the lowercase function name (e.g.
    ``"sma"`` or ``"macd"``). Call ``.alias(...)`` on the returned expression
    when multiple instances need distinct names. Multi-output factories return
    a single ``pl.struct(...)`` Expr; the view's ``eval`` unnests it into a
    DataFrame at evaluation time.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if args and isinstance(args[0], pl.Expr):
            if "src" in kwargs:
                raise ValueError("Cannot specify 'src' as keyword when first arg is a pl.Expr")
            kwargs["src"] = args[0]
            args = args[1:]

        result = func(*args, **kwargs)
        return result.alias(func.__name__.lower())

    return wrapper
