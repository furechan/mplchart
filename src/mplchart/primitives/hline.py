"""HLine primitive"""

import matplotlib as mpl

from ..model import Primitive


class HLine(Primitive):
    """Horizontal line on the current pane at a given value.

    Args:
        value: y-axis value for the horizontal line position
        color: line color (default: matplotlib grid.color)
        linestyle: line style (default: matplotlib grid.linestyle)

    Examples:
        chart.plot(Pane("below"), RSI(14), HLine(70, color="red"), HLine(30, color="green"))
        chart.hline(70, color="red")
    """

    def __init__(self, value, *, color=None, linestyle=None):
        self.value = value
        self.color = color
        self.linestyle = linestyle

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.get_axes("same")

        color = self.color or mpl.rcParams["grid.color"]
        linestyle = self.linestyle or mpl.rcParams["grid.linestyle"]

        ax.axhline(self.value, color=color, linestyle=linestyle)
