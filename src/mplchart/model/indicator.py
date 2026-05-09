"""Indicator base classes — pandas-only."""

import pandas as pd

from abc import ABC, abstractmethod

from ..utils import short_repr, get_series




class Indicator(ABC):
    """Abstract base class for technical analysis indicators.

    Subclasses implement ``__call__(prices)`` to compute indicator values from
    a prices DataFrame and return a Series or DataFrame. Subclasses that return
    a multi-column DataFrame should set ``output_names`` to the tuple of column
    names so that single-output APIs (e.g. ``as_expr``) can reject them.

    Use ``@`` to bind an indicator to a rendering primitive, and ``|`` to
    chain indicators or apply to data::

        RSI(14) @ LinePlot(overbought=70)  # bind to a primitive
        SMA(50) | EMA(20)                  # chain: apply SMA then EMA
        prices  | SMA(50)                  # apply indicator to data
    """

    __repr__ = short_repr

    output_names: tuple[str, ...] | None = None

    @abstractmethod
    def __call__(self, prices):
        """Compute the indicator value.

        Args:
            prices (DataFrame): OHLCV prices DataFrame with a datetime index.

        Returns:
            Series or DataFrame: Computed indicator values aligned to the
            prices index.
        """
        ...

    __pandas_priority__ = 5000

    # __or__ handles composition only: ``indicator | indicator`` → IndicatorChain.
    def __or__(self, other):
        if isinstance(other, Indicator):
            return IndicatorChain(self, other)
        return NotImplemented

    # __ror__ handles application only: ``data | indicator`` → indicator(data).
    def __ror__(self, other):
        if isinstance(other, (pd.DataFrame, pd.Series)):
            return self(other)
        raise TypeError(
            f"| applies an indicator to a pandas DataFrame or Series; "
            f"got {type(other).__name__} on the left."
        )

    def get_series(self, data):
        item = getattr(self, "item", None)
        return get_series(data, item=item)

    def as_expr(self, item: str | None = None):
        """Wrap this indicator as a pandas ``Expression``.

        Enables boolean composition with pandas columns, e.g.
        ``RSI(14).as_expr() > 30``. For multi-output indicators, pass ``item``
        to select one column: ``MACD().as_expr("macdhist") > 0``.

        Requires pandas >= 3.0.
        """
        if self.output_names:
            if item is None:
                names = ", ".join(self.output_names)
                raise TypeError(
                    f"as_expr() on multi-output {self!r} requires an item; "
                    f"available: {names}."
                )
            if item not in self.output_names:
                names = ", ".join(self.output_names)
                raise ValueError(
                    f"{item!r} is not an output of {self!r}; available: {names}."
                )
        elif item is not None:
            raise TypeError(
                f"as_expr(item=...) only applies to multi-output indicators; "
                f"{self!r} is single-output."
            )

        try:
            from pandas.api.typing import Expression
        except ImportError as exc:
            raise RuntimeError(
                f"as_expr() requires pandas >= 3.0 (got {pd.__version__}); "
                "the Expression API was introduced in pandas 3.0."
            ) from exc

        if item is None:
            return Expression(self, repr(self))
        return Expression(lambda prices: self(prices)[item], f"{self!r}.{item}")



class IndicatorChain(Indicator):
    """An indicator formed by chaining two or more indicators left-to-right.

    Created by the ``|`` operator between indicators. Applied left-to-right,
    so ``ind1 | ind2`` first applies ``ind1`` and then passes the result to
    ``ind2``.

    Example:
        EMA(10) | ROC(1)   # compute EMA(10) then compute ROC on that
    """

    def __init__(self, *args):
        chain = []
        for arg in args:
            if isinstance(arg, IndicatorChain):
                chain.extend(arg.args)
            elif isinstance(arg, Indicator):
                chain.append(arg)
            else:
                raise TypeError("IndicatorChain accepts Indicator instances only")
        self.args = tuple(chain)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return " | ".join(repr(fn) for fn in self.args)

    def __call__(self, prices):
        result = prices
        for fn in self.args:
            result = fn(result)
        return result
