"""Expression prelude — constants and wrap_expression decorator"""

import inspect
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

    Automatically adds an alias to single-expression results, e.g. "sma-20",
    "rsi-14". Multi-expression results (tuples) are left as-is since they
    carry explicit aliases.
    """
    sig = inspect.signature(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        if args and isinstance(args[0], pl.Expr):
            if "src" in kwargs:
                raise ValueError("Cannot specify 'src' as keyword when first arg is a pl.Expr")
            kwargs["src"] = args[0]
            args = args[1:]

        result = func(*args, **kwargs)

        if isinstance(result, pl.Expr):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            periods = [
                v for k, v in bound.arguments.items()
                if k not in ("src", "high", "low") and isinstance(v, (int, float))
            ]
            name = func.__name__.lower()
            alias = "-".join([name] + [str(p) for p in periods]) if periods else name
            result = result.alias(alias)

        return result

    return wrapper
