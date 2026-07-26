"""Pane primitive"""

from ..canvas import PanePosition
from ..model.primitive import Primitive


class Pane(Primitive):
    """
    Pane Primitive

    Create a new pane inline within a plot() call. Mirrors the
    ``chart.pane()`` method.

    Creation is sticky: the new pane becomes current and the primitives
    that follow land on it. Pane is the only pane creator — to draw a
    single primitive on an existing pane use the renderers' ``pane=``
    parameter instead (e.g. ``LinePlot(x, pane="main")``).

    Args:
        position (str): "below" (default) or "above" — where the new pane
            is inserted in the vertical stack
        height_ratio (float): relative height of the new pane
        yticks (tuple): y-axis tick values (also draws heavy grid lines)

    Examples:
        chart.plot(Pane("below", yticks=(30, 50, 70)), LinePlot(RSI(14)))
    """

    def __init__(self, position: PanePosition = "below", *, height_ratio: float | None = None, yticks: tuple | None = None):
        self.position = position
        self.height_ratio = height_ratio
        self.yticks = yticks

    def apply_to_chart(self, chart):
        ax = chart.canvas.new_axes(self.position, height_ratio=self.height_ratio)

        if self.yticks:
            ax.set_yticks(self.yticks)
            ax.grid(axis="y", which="major", linestyle="-", linewidth=2)
