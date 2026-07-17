"""Primitive base classes — backend-agnostic."""

import copy
import warnings

from abc import ABC, abstractmethod

from ..utils import short_repr, is_indicator_like




class Primitive(ABC):
    """Abstract base class for chart primitives.

    Primitives act directly on the chart without going through the indicator
    calculation pipeline. They implement ``apply_to_chart`` which is invoked
    before any indicator calculation takes place.

    Primitives support the ``@`` operator to bind an indicator or expression::

        SMA(50) @ LinePlot(style="dashed", color="blue")   # indicator
        RSI()   @ LinePlot(overbought=70)                  # polars expression
    """

    __repr__ = short_repr

    @abstractmethod
    def apply_to_chart(self, chart) -> None:
        """Act on the chart — draw, create a pane, or otherwise modify it.

        Called before any indicator calculation. Prices are available as
        ``chart.prices`` (full, unsliced); use ``chart.slice(data)`` to
        restrict data to the current view window and ``chart.get_axes()``
        to obtain or create the target pane.

        Args:
            chart (Chart): The parent chart instance.
        """
        ...

    def clone(self, **kwargs):
        result = copy.copy(self)
        vars(result).update(kwargs)
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
