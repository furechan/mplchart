""" Price primitive """

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

    def __init__(self, item: str = 'close', *, color: str = None):
        self.item = item
        self.color = color

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        data = series_data(prices, self.item)
        data = chart.extract_df(data)

        label = self.item
        color = self.color

        xv, yv = series_xy(data)
        ax.plot(xv, yv, label=label, color=color)
