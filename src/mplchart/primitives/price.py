"""Price primitive"""

from matplotlib import pyplot as plt

from ..model import Primitive
from ..utils import series_xy
from ..library import calc_price


class Price(Primitive):
    """
    Price Primitive

    Used to plot price as a line plot

    Args:
        item (str) :  name of the price item. default 'close'
        One of 'open', 'high', 'low', 'close', 'avg', 'mid', 'typ', 'wcl', ...

    Example:
        Price('close')  # plot the close price series
        Price('open')   # plot the open price series
    """

    same_scale: bool = True

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


    def __call__(self, prices):
        return calc_price(prices, self.item)


    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        data = self(prices)
        data = chart.slice(data)

        textcolor = plt.rcParams["text.color"]

        label = repr(self)
        width = self.width
        alpha = self.alpha
        color = self.color or textcolor

        xv, yv = series_xy(data)
        ax.plot(xv, yv, label=label, linewidth=width, alpha=alpha, color=color)
