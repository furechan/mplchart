"""Peaks primitive"""

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

from ..model import Primitive


class Peaks(Primitive):
    """Peaks primitive.

    Plots local peak (high) and valley (low) points as scatter markers on the
    chart. A point is considered a local peak or valley if it is the highest
    high (or lowest low) within a window of ``2 * span + 1`` bars centered on
    that bar.

    Args:
        span (int): Minimum number of bars required on each side of a local
            extremum for it to qualify as a peak or valley. Defaults to 1.
        item (str, optional): Column name to use as the price series for peak
            detection. If ``None``, uses the ``high``/``low`` columns of the
            prices DataFrame.
        color (str, optional): Marker color. Defaults to the current
            ``text.color`` matplotlib parameter.
    """

    indicator = None

    def __init__(self, span=1, *, item: str | None = None, color: str | None = None):
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

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        data = chart.calc_result(prices, self.indicator)
        data = self.process(data)
        data = chart.slice(data)

        # xy, yv = series_xy(data)
        xv, yv = data.index, data
        color = self.color or plt.rcParams["text.color"]

        ax.scatter(xv, yv, c=color, s=10 * 10, alpha=0.5, marker=".")


def extract_peaks(prices, span=1):
    """Extract local peak and valley points from a price series or DataFrame.

    Args:
        prices (Series or DataFrame): Price data. If a DataFrame, the ``high``
            and ``low`` columns are used; otherwise the same series is used for
            both high and low detection.
        span (int): Minimum number of bars required on each side of a local
            extremum. Defaults to 1.

    Returns:
        Series: Price values at local peaks and valleys only; all other
        positions are dropped (not NaN — the series is sparse).
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
