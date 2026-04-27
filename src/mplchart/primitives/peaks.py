"""Peaks primitive"""

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

import matplotlib.pyplot as plt

from ..model import BindingPrimitive
from ..utils import col_to_numpy


class Peaks(BindingPrimitive):
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

    def __init__(self, span=1, *, item: str | None = None, color: str | None = None):
        super().__init__(None)
        self.span = span
        self.color = color
        self.item = item

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        data = chart.calc_result(prices, self.indicator)

        # Reduce by item first, if requested — yields a Series.
        if self.item is not None and hasattr(data, "columns"):
            data = data[self.item]

        if hasattr(data, "columns"):
            # DataFrame — peaks on high, valleys on low.
            windowed = chart.slice(data, xcol="xloc")
            xv = np.asarray(windowed["xloc"])
            hi = np.asarray(col_to_numpy(windowed, "high"), dtype=float)
            lo = np.asarray(col_to_numpy(windowed, "low"), dtype=float)
        else:
            # Series — same values for peaks and valleys.
            xv, arr = chart.mapper.series_xy(data)
            arr = np.asarray(arr, dtype=float)
            hi = lo = arr

        row_indices, values = extract_peaks(hi, lo, span=self.span)
        xv = xv[row_indices]

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
