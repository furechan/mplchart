"""ZigZag Primitive"""

import numpy as np

from ..model import Primitive
from ..utils import col_to_numpy


def calc_zigzag(prices, threshold=5.0):
    """Compute ZigZag pivot points from OHLC prices.

    Identifies successive swing highs and lows where each reversal exceeds the
    given percentage threshold from the previous pivot.

    Args:
        prices (DataFrame): OHLCV prices DataFrame with ``high``, ``low``, and
            ``close`` columns.
        threshold (float): Minimum percentage move required to confirm a
            reversal. Defaults to 5.0.

    Returns:
        tuple[np.ndarray, np.ndarray]: (row_indices, values) of pivot points.
    """
    high = np.asarray(col_to_numpy(prices, "high"), dtype=float)
    low = np.asarray(col_to_numpy(prices, "low"), dtype=float)
    close = np.asarray(col_to_numpy(prices, "close"), dtype=float)

    pi = pv = pdir = None
    index = []
    values = []

    for i in range(len(close)):
        h, lo, c = high[i], low[i], close[i]

        if pdir is None:
            pi, pv, pdir = i, c, 0

        elif pdir == 0:
            higher = h / pv - 1 > threshold / 100
            lower = lo / pv - 1 < -threshold / 100

            if higher and not lower:
                pi, pv, pdir = i, h, +1
            if lower and not higher:
                pi, pv, pdir = i, lo, -1

        elif pdir > 0:
            higher = h / pv - 1 > 0
            lower = lo / pv - 1 < -threshold / 100

            if higher:
                pi, pv, pdir = i, h, +1
            elif lower:
                index.append(pi)
                values.append(pv)
                pi, pv, pdir = i, lo, -1

        elif pdir < 0:
            higher = h / pv - 1 > threshold / 100
            lower = lo / pv - 1 < 0

            if lower:
                pi, pv, pdir = i, lo, -1
            elif higher:
                index.append(pi)
                values.append(pv)
                pi, pv, pdir = i, h, +1

    return np.array(index, dtype=int), np.array(values, dtype=float)


class ZigZag(Primitive):
    """ZigZag primitive.

    Plots a line connecting successive swing highs and lows, filtering out
    moves smaller than a percentage threshold. Rendered on the same scale as
    the price series.

    Args:
        threshold (float): Minimum percentage reversal required to register a
            new pivot. Defaults to 5.0.
    """

    same_scale = True

    def __init__(self, threshold=5.0):
        self.threshold = threshold

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        window = chart.mapper.calc_window()
        chart.window = window

        # run zigzag on the windowed slice; returned indices are 0-based within window
        windowed = chart.slice(prices) if hasattr(prices, "index") else prices[window]
        row_indices, values = calc_zigzag(windowed, threshold=self.threshold)

        # map local indices to absolute rownums
        xv = chart.mapper.rownum[window][row_indices]
        label = repr(self)
        ax.plot(xv, values, label=label, color=None)
