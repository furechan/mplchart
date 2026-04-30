"""Pane primitive"""

from ..model import Primitive


class Pane(Primitive):
    """
    Pane Primitive

    Create or select a pane inline within a plot() call.
    Mirrors the chart.pane() method but usable as a primitive in the indicator list.

    Args:
        target (str): target pane as 'same', 'above', 'below', 'twinx'
        height_ratio (float): relative height of the new pane
        yticks (tuple): y-axis tick values (also draws heavy grid lines)

    Examples:
        chart.plot(Pane("below", yticks=(30, 50, 70)), RSI(14) @ LinePlot())
    """

    def __init__(self, target="below", *, height_ratio=None, yticks=None):
        self.target = target
        self.height_ratio = height_ratio
        self.yticks = yticks

    def plot_handler(self, prices, chart, ax=None):
        ax = chart.get_axes(self.target, height_ratio=self.height_ratio)

        if self.yticks:
            ax.set_yticks(self.yticks)
            ax.grid(axis="y", which="major", linestyle="-", linewidth=2)
