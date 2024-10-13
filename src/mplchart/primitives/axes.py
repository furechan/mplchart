"""Axes primitives"""

import warnings

from ..model import Primitive


class SameAxes(Primitive):
    """Primitive to force same axis for next indicator"""

    def __init__(self):
        warnings.warn(
            "SameAxes primitive is deprecated. Use Position modifier instead!",
            DeprecationWarning,
            stacklevel=2,
        )

    def plot_handler(self, data, chart, ax=None):
        chart.force_target("same")


class NewAxes(Primitive):
    """Primitive to force axis for next indicator"""

    def __init__(self, target="below"):
        warnings.warn(
            "NewAxes primitive is deprecated. Use Position modifier instead!",
            DeprecationWarning,
            stacklevel=2,
        )

        if target not in ("twinx", "above", "below"):
            raise ValueError(f"Invalid target {target!r}")

        self.target = target

    def plot_handler(self, data, chart, ax=None):
        chart.force_target(self.target)
