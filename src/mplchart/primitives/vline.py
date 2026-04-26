"""VLine primitive"""

import matplotlib as mpl

from ..model import Primitive


class VLine(Primitive):
    """Vertical line across all panes at a given date.

    Args:
        date: date or date string for the vertical line position
        color: line color (default: matplotlib grid.color)
        linestyle: line style (default: matplotlib grid.linestyle)

    Examples:
        chart.plot(Candlesticks(), VLine("2024-01-15"))
        chart.vline("2024-01-15", color="red")
    """

    def __init__(self, date, *, color=None, linestyle=None):
        self.date = date
        self.color = color
        self.linestyle = linestyle

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.root_axes()

        color = self.color or mpl.rcParams["grid.color"]
        linestyle = self.linestyle or mpl.rcParams["grid.linestyle"]

        xv = chart.map_date(self.date)
        ax.axvline(xv, color=color, linestyle=linestyle)
