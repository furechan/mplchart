"""Primitive base classes — backend-agnostic."""

import copy
import warnings

from abc import ABC, abstractmethod

from ..utils import short_repr, is_indicator_like




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
