"""primitive base class"""

import copy
import warnings

from abc import ABC, abstractmethod

from .utils import short_repr, get_series, is_indicator_like




class Primitive(ABC):
    """Abstract base class for chart primitives.

    Primitives draw directly from the raw prices DataFrame without going through
    the indicator calculation pipeline. They implement ``plot_handler`` which is
    invoked before any indicator calculation takes place.

    Primitives support the ``@`` operator to bind an indicator or expression::

        SMA(50) @ LinePlot(style="dashed", color="blue")   # indicator
        RSI()   @ LinePlot(overbought=70)                  # polars expression
    """

    __repr__ = short_repr

    @abstractmethod
    def plot_handler(self, prices, chart, ax=None):
        """Draw the primitive onto the chart.

        Called before any indicator calculation. The prices DataFrame has not
        been sliced yet; use ``chart.slice(data)`` to restrict the data to the
        current view window.

        Args:
            prices (DataFrame): Full (unsliced) OHLCV prices DataFrame.
            chart (Chart): The parent chart instance.
            ax (Axes, optional): Target axes. If ``None``, the primitive should
                call ``chart.get_axes()`` to obtain or create the target pane.
        """
        ...

    def clone(self, **kwargs):
        result = copy.copy(self)
        result.__dict__.update(self.__dict__, **kwargs)
        return result

class BindingPrimitive(Primitive):
    """Base class for primitives that bind to an indicator or expression via ``@``.

    Provides the ``indicator`` attribute, a positional ``indicator`` argument,
    and the ``@`` binding operator.
    """

    indicator = None

    def __init__(self, indicator=None):
        self.indicator = indicator

    def __rmatmul__(self, other):
        if not is_indicator_like(other):
            return NotImplemented
        return self.clone(indicator=other)

    def __ror__(self, indicator):
        if not callable(indicator):
            return NotImplemented
        warnings.warn("Use @ to bind an indicator to a primitive.", DeprecationWarning, stacklevel=2)
        return self.clone(indicator=indicator)


class Indicator(ABC):
    """Abstract base class for technical analysis indicators.

    Subclasses implement ``__call__(prices)`` to compute indicator values from
    a prices DataFrame and return a Series or DataFrame.

    Use ``@`` to bind an indicator to a rendering primitive, and ``|`` to
    chain indicators or apply to data::

        RSI(14) @ LinePlot(overbought=70)  # bind to a primitive
        SMA(50) | EMA(20)                  # chain: apply SMA then EMA
        prices  | SMA(50)                  # apply indicator to data
    """

    __repr__ = short_repr

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

    def __or__(self, other):
        if callable(other):
            return IndicatorChain(self, other)
        return NotImplemented

    def __ror__(self, other):
        if isinstance(other, Indicator):
            return IndicatorChain(other, self)
        return self(other)

    def get_series(self, data):
        item = getattr(self, "item", None)
        return get_series(data, item=item)



class IndicatorChain(Indicator):
    """An indicator formed by chaining two or more indicators left-to-right.

    Created by the ``|`` operator between indicators. Applied left-to-right,
    so ``ind1 | ind2`` first applies ``ind1`` and then passes the result to
    ``ind2``.

    Example:
        EMA(10) | ROC(1)   # compute EMA(10) then compute ROC on that
    """

    def __init__(self, *args):
        if not all(callable(arg) for arg in args):
            raise TypeError("Arguments must be callable")
        self.args = args

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return " | ".join(repr(fn) for fn in self.args)

    def __call__(self, prices):
        result = prices
        for fn in self.args:
            result = fn(result)
        return result

    def __ror__(self, other):
        if isinstance(other, Indicator):
            return self.__class__(other, *self.args)
        return self(other)


