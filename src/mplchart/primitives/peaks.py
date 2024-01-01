""" Peaks primitive """

import numpy as np
import pandas as pd

from ..model import Primitive


def extract_peaks(prices, span=1):
    """
    extracts local peaks.

    Args:
        span (int) : refers to minimum number bars required before
        and after the local peak

    Return:
        A series of prices defined only at local peaks and equal to nan otherwize
    """

    window = 2 * span + 1

    if hasattr(prices, "columns"):
        high, low = prices.high, prices.low
    else:
        high, low = prices, prices

    peaks = pd.Series(np.nan, prices.index)

    mask = high.rolling(window).max().shift(-span) == high
    peaks.mask(mask, high, inplace=True)

    mask = low.rolling(window).min().shift(-span) == low
    peaks.mask(mask, low, inplace=True)

    return peaks.dropna()


class Peaks(Primitive):
    """
    Peeks Primitive
    Used to plot peaks and valey points

    Args:
        span (int) :  minimum number bars required before and after the local peak

    """

    indicator = None

    COLOR = "blue"

    def __init__(self, span=1, *, item=None, color=None):
        self.span = span
        self.color = color
        self.item = item

    def __ror__(self, indicator):
        if not callable(indicator):
            return NotImplemented

        self.clone(indicator=indicator)

    def calc(self, data):
        if self.item:
            data = getattr(data, self.item)
        return extract_peaks(data, span=self.span)

    def plot_handler(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        indicator = self.indicator or chart.last_indicator

        if indicator:
            data = indicator(data)

        data = self.calc(data)
        data = chart.extract_df(data)

        xv = data.index
        yv = data

        color = self.color or chart.get_setting("peaks", "color", self.COLOR)

        ax.scatter(xv, yv, c=color, s=10 * 10, alpha=0.5, marker=".")
