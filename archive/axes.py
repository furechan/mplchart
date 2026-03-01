"""Axes primitives"""

import copy
import warnings

from ..model import Primitive


class NewAxes(Primitive):
    """New Axes Primitive

    Apply to an indicator with the `|` operator.

    Args:
        target (str) : target axes like 'same', 'above', 'below'

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
        result.target_pane = self.target
        return result

    def plot_handler(self, prices, chart, ax=None):
        warnings.warn(
            "Use without indicator is deprecated. Use with `|` operator!",
            DeprecationWarning,
            stacklevel=2,
        )
        chart.force_target(self.target)


class SameAxes(NewAxes):
    """Use Same Axes

    Apply to an indicator with the `|` operator.

    Example:
        ROC(20) | SameAxes()
    """

    def __init__(self):
        super().__init__("same")
