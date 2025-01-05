"""Peaks primitive"""

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

from ..model import Primitive


class Peaks(Primitive):
    """
    Peeks Primitive
    Used to plot peaks and valey points

    Args:
        span (int) :  minimum number bars required before and after the local peak

    """

    indicator = None

    def __init__(self, span=1, *, item: str = None, color: str = None):
        self.span = span
        self.color = color
        self.item = item

    def __ror__(self, indicator):
        if not callable(indicator):
            return NotImplemented

        self.clone(indicator=indicator)

    def process(self, data):
        if self.item:
            data = getattr(data, self.item)
        return extract_peaks(data, span=self.span)

    def plot_handler(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        data = chart.calc_result(data, self.indicator)
        data = self.process(data)
        data = chart.slice(data)

        xv, yv = data.index, data
        color = self.color or plt.rcParams["text.color"]

        ax.scatter(xv, yv, c=color, s=10 * 10, alpha=0.5, marker=".")


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
        high, low = prices["high"], prices["low"]
    else:
        high, low = prices, prices

    peaks = pd.Series(np.nan, prices.index)

    mask = high.rolling(window, center=True).max() == high
    peaks.mask(mask, high, inplace=True)

    mask = low.rolling(window, center=True).min() == low
    peaks.mask(mask, low, inplace=True)

    return peaks.dropna()
