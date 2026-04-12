"""Peaks primitive"""

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

import matplotlib.pyplot as plt

from ..model import Primitive
from ..utils import col_to_numpy


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
        return self.clone(indicator=indicator)

    def process(self, data):
        if self.item:
            arr = np.asarray(col_to_numpy(data, self.item), dtype=float)
            return extract_peaks(arr, arr, span=self.span)
        high = np.asarray(col_to_numpy(data, "high"), dtype=float)
        low = np.asarray(col_to_numpy(data, "low"), dtype=float)
        return extract_peaks(high, low, span=self.span)

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        window = chart.mapper.calc_window()
        chart.window = window

        data = chart.calc_result(prices, self.indicator)
        windowed = chart.slice(data) if hasattr(data, "index") else data[window]
        row_indices, values = self.process(windowed)

        # map local indices to absolute rownums
        xv = chart.mapper.rownum[window][row_indices]
        color = self.color or plt.rcParams["text.color"]
        ax.scatter(xv, values, c=color, s=10 * 10, alpha=0.5, marker=".")


def extract_peaks(high, low, span=1):
    """Extract local peak and valley row indices from high/low numpy arrays.

    Args:
        high (np.ndarray): High prices.
        low (np.ndarray): Low prices.
        span (int): Half-window size. A point qualifies if it is the extremum
            within ``2 * span + 1`` bars centered on it.

    Returns:
        tuple[np.ndarray, np.ndarray]: (row_indices, values) of peaks and valleys.
    """
    window = 2 * span + 1

    # pad edges to keep output length == n
    padded_high = np.pad(high, span, mode="edge")
    padded_low = np.pad(low, span, mode="edge")

    roll_max = sliding_window_view(padded_high, window).max(axis=1)
    roll_min = sliding_window_view(padded_low, window).min(axis=1)

    peak_mask = high == roll_max
    valley_mask = low == roll_min
    combined = peak_mask | valley_mask

    row_indices = np.where(combined)[0]
    values = np.where(peak_mask[row_indices], high[row_indices], low[row_indices])

    return row_indices, values
