"""Price primitive"""

from matplotlib import pyplot as plt

from ..model import Primitive
from ..utils import series_data, series_xy


class Price(Primitive):
    """
    Price Primitive

    Used to plot price as a line plot

    Args:
        item (str) :  name of the column to plot. default 'close'

    Example:
        Price('close')  # plot the close price series
        Price('open')   # plot the open price series
    """

    def __init__(
        self,
        item: str = "close",
        *,
        width: float = 1.0,
        alpha: float = 1.0,
        color: str = None,
    ):
        self.item = item
        self.width = width
        self.alpha = alpha
        self.color = color

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        data = series_data(prices, self.item)
        data = chart.extract_df(data)

        textcolor = plt.rcParams["text.color"]

        label = self.item
        width = self.width
        alpha = self.alpha
        color = self.color or textcolor

        xv, yv = series_xy(data)
        ax.plot(xv, yv, label=label, linewidth=width, alpha=alpha, color=color)
