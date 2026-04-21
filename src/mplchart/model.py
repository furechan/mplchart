"""primitive base class"""

import copy

from types import MappingProxyType
from abc import ABC, abstractmethod

from .utils import short_repr, get_series, is_indicator_like



class Wrapper(ABC):
    """Abstract base class for indicator plotting wrappers.

    A ``Wrapper`` is returned by an ``Indicator.__call__`` when the indicator
    wants to take full control of how its result is rendered. The chart calls
    ``plot_result`` with the already-sliced data instead of delegating to
    the default ``AutoPlot`` primitive.
    """

    @abstractmethod
    def plot_result(self, data, chart, ax=None): ...


class Primitive(ABC):
    """Abstract base class for chart primitives.

    Primitives draw directly from the raw prices DataFrame without going through
    the indicator calculation pipeline. They implement ``plot_handler`` which is
    invoked before any indicator calculation takes place.

    Primitives support the ``|`` operator to compose them with an indicator::

        SMA(50) | LinePlot(style="dashed", color="blue")
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

    def clone_legacy(self, **kwargs):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__, **kwargs)
        return result

    def clone(self, **kwargs):
        result = copy.copy(self)
        result.__dict__.update(self.__dict__, **kwargs)
        return result

    def __rmatmul__(self, other):
        if isinstance(other, Indicator):
            import warnings
            warnings.warn(
                "Use | to bind an indicator to a primitive. @ is for polars expressions.",
                DeprecationWarning, stacklevel=2,
            )
            return self.clone(indicator=other)
        if not is_indicator_like(other):
            return NotImplemented
        return self.clone(indicator=other)


class Indicator(ABC):
    """Abstract base class for technical analysis indicators.

    Subclasses implement ``__call__(prices)`` to compute indicator values from
    a prices DataFrame and return a Series or DataFrame.

    Indicators support the ``@`` operator for composition and for applying an
    indicator to data directly::

        # Compose two indicators (applied right-to-left):
        SMA(20) @ EMA(10)   # applies EMA first, then SMA

        # Apply an indicator to prices directly:
        SMA(20) @ prices    # equivalent to SMA(20)(prices)
    """

    __repr__ = short_repr

    def __init_subclass__(cls, **kwargs):
        """Save indicator extra kwargs as info dictionary"""
        if kwargs:
            cls.info = MappingProxyType(kwargs)

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

    def __matmul__(self, other):
        import warnings
        if isinstance(other, Primitive):
            return NotImplemented
        if callable(other):
            warnings.warn(
                "Composing indicators with @ is deprecated. Use | for chaining.",
                DeprecationWarning, stacklevel=2,
            )
            return ComposedIndicator(self, other)
        warnings.warn(
            "Applying indicators with @ is deprecated. Use indicator(data) instead.",
            DeprecationWarning, stacklevel=2,
        )
        return self(other)

    __pandas_priority__ = 5000

    def __ror__(self, other):
        if isinstance(other, Indicator):
            return IndicatorChain(other, self)
        return self(other)

    def apply(self, other):
        """Apply this indicator to data or compose with another indicator.

        Args:
            other: A prices DataFrame to compute the indicator on,
                   or another indicator to compose with (applied first).

        Returns:
            Computed result if other is data, or a ComposedIndicator.
        """
        if callable(other):
            return ComposedIndicator(self, other)
        return self(other)

    def get_series(self, data):
        item = getattr(self, "item", None)
        return get_series(data, item=item)


class ComposedIndicator(Indicator):
    """An indicator formed by composing two or more indicators in sequence.

    Created by the ``@`` operator. Indicators are applied right-to-left, so
    ``ind1 @ ind2`` first applies ``ind2`` and then passes the result to
    ``ind1``.

    Example:
        SMA(20) @ EMA(10)   # compute EMA(10) then smooth with SMA(20)
    """

    def __init__(self, *args):
        if not all(callable(arg) for arg in args):
            raise TypeError("Arguments must be callable")
        self.args = args

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return " @ ".join(repr(fn) for fn in self.args)

    def __call__(self, prices):
        result = prices
        for fn in reversed(self.args):
            result = fn(result)
        return result

    def __matmul__(self, other):
        if callable(other):
            return self.__class__(*self.args, other)
        return self(other)


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


