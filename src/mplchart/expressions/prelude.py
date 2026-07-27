"""Expression prelude — constants and wrap_expression decorator"""

import inspect
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


def _build_label(func, args, kwargs, sig):
    """Build a slug label like 'macd-12-26-9' from bound call arguments."""
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    periods = [
        v for k, v in bound.arguments.items()
        if k not in ("src", "high", "low") and isinstance(v, (int, float))
    ]
    name = func.__name__.lower()
    return "-".join([name] + [str(p) for p in periods]) if periods else name


def wrap_expression(func):
    """Decorator for expression factory functions.

    Allows the first positional argument to be a pl.Expr, which is then
    passed as the `src` keyword argument. This enables both calling styles:

        SMA(20, pl.col("close"))   # positional expr
        SMA(20)                    # defaults to CLOSE
        SMA(20, src=pl.col("open"))

    Builds a slug label (e.g. "sma-20", "macd-12-26-9") from the call args
    and aliases the resulting ``pl.Expr`` with it. Multi-output factories
    return a single ``pl.struct(...)`` Expr; the view's ``eval`` unnests
    it into a DataFrame at evaluation time.
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
        label = _build_label(func, args, kwargs, sig)
        return result.alias(label)

    return wrapper
