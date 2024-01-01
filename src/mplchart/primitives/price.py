""" Price primitive """

import pandas as pd

from ..model import Primitive
from ..utils import series_xy


class Price(Primitive):
    """
    Price Primitive

    Used to plot price as a line plot

    Args:
        item (str) :  name of the column to plot. default 'close'

    Returns:
        the series of given name

    Example:
        Price('close') the close price series
        Price('open') the open price series

    """

    def __init__(self, *, item="close"):
        self.item = item

    def __str__(self):
        return self.item

    def calc(self, data):
        if isinstance(data, pd.DataFrame):
            data = data[self.item]
        return data

    def plot_handler(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        label = str(self)

        data = self.calc(data)
        data = chart.extract_df(data)

        xv, yv = series_xy(data)
        ax.plot(xv, yv, label=label, color=None)
