"""Expression prelude — constants and wrap_expression decorator"""

import polars as pl
from functools import wraps


OPEN   = pl.col("open")
HIGH   = pl.col("high")
LOW    = pl.col("low")
CLOSE  = pl.col("close")
VOLUME = pl.col("volume")


def wrap_expression(func):
    """Decorator for expression factory functions.

    Allows the first positional argument to be a pl.Expr, which is then
    passed as the `src` keyword argument. This enables both calling styles:

        SMA(20, pl.col("close"))   # positional expr
        SMA(20)                    # defaults to CLOSE
        SMA(20, src=pl.col("open"))
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if args and isinstance(args[0], pl.Expr):
            if "src" in kwargs:
                raise ValueError("Cannot specify 'src' as keyword when first arg is a pl.Expr")
            kwargs["src"] = args[0]
            args = args[1:]
        return func(*args, **kwargs)

    return wrapper
