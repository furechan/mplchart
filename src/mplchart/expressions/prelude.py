"""Expression prelude — constants and wrap_expression decorator"""

import inspect
import polars as pl
from functools import wraps


OPEN   = pl.col("open")
HIGH   = pl.col("high")
LOW    = pl.col("low")
CLOSE  = pl.col("close")
VOLUME = pl.col("volume")


class ExprBundle(tuple):
    """Tuple of ``pl.Expr`` returned by multi-output expression factories.

    Subclasses ``tuple`` so unpacking still works
    (``macd, signal, hist = MACD(12, 26, 9)``) while carrying a ``label``
    attribute used as ``__repr__`` — e.g. ``macd-12-26-9``. AutoPlotter
    uses the label to identify the indicator group.
    """

    label: str

    def __new__(cls, items, *, label: str):
        obj = super().__new__(cls, items)
        obj.label = label
        return obj

    def __repr__(self) -> str:
        return self.label


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

    Builds a slug label (e.g. "sma-20", "macd-12-26-9") from the call args.
    Single-expression results get ``.alias(label)`` applied. Multi-expression
    results are wrapped in an ``ExprBundle`` whose ``__repr__`` returns the
    label, so AutoPlotter can identify the indicator group.
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

        if isinstance(result, pl.Expr):
            return result.alias(label)

        if isinstance(result, tuple):
            return ExprBundle(result, label=label)

        return result

    return wrapper
