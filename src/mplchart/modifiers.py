"""Indicator Modifiers"""

import copy

from collections.abc import Mapping

from .utils import get_name


class NewAxes:
    """New Axes Modifier

    Apply to an indicator with the `|` operator.

    Args:
        target: one of 'same', 'above', 'below'

    Example:
        SMA(20) | NewAxes()
    """

    def __init__(self, target="below"):
        if target not in ("same", "twinx", "above", "below"):
            raise ValueError(f"Invalid target {target!r}")
        self.target = target

    def __ror__(self, indicator):
        if not callable(indicator):
            return NotImplemented
        
        result = copy.copy(indicator)
        result.default_pane = self.target
        return result


class SameAxes(NewAxes):
    """Use Same Axes

    Apply to an indicator with the `|` operator.

    Example:
        ROC(20) | SameAxes()
    """

    def __init__(self):
        super().__init__("same")


class Color:
    """Color Modifier

    Apply to an indicator with the `|` operator.

    Args:
        color (str) : main color
        **kwargs : colors with lowercase keys

    Example:
        SMA() | Color("red")
        MACD() | Color(macdhist="blue")
    """

    def __init__(self, color=None, **kwargs):
        self.color = color
        self.kwargs = kwargs

    def __ror__(self, indicator):
        if not callable(indicator):
            return NotImplemented
        
        colors = getattr(indicator, 'colors', {})
        if not isinstance(colors, Mapping):
            raise TypeError("colors attribute is a ot a mapping!")
        colors = dict(colors)

        if self.color:
            name = get_name(indicator).lower()
            self.kwargs[name] = self.color
        colors.update(self.kwargs)

        result = copy.copy(indicator)
        result.colors = colors
        return result

