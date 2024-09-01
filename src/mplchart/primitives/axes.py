""" Axes primitives """

from ..model import Primitive


class ForceAxes(Primitive):
    """Primitive to force axis for next indicator"""

    def __init__(self, target="below"):
        if target not in ("samex", "twinx", "above", "below"):
            raise ValueError(f"Invalid target {target!r}")

        self.target = target

    def plot_handler(self, data, chart, ax=None):
        chart.force_target(self.target)


class NewAxes(ForceAxes):
    """Primitive to force new axis for next indicator"""

    def __init__(self, target="below"):
        if target not in ("above", "below"):
            raise ValueError(f"Invalid target {target!r}")

        super().__init__(target)


class SameAxes(ForceAxes):
    """Primitive to force same axis for next indicator"""

    def __init__(self):
        super().__init__("samex")
