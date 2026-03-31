"""ZigZag Primitive"""

import pandas as pd
from ..model import Primitive
from ..utils import series_xy


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
        Series: Pivot prices (highs and lows) at each identified swing point,
        indexed by the corresponding row in ``prices``.
    """
    pi = pv = pdir = None
    index = []
    values = []

    for i, row in enumerate(prices.itertuples()):
        if pdir is None:
            pi, pv, pdir = i, row.close, 0

        elif pdir == 0:
            higher = row.high / pv - 1 > threshold / 100
            lower = row.low / pv - 1 < -threshold / 100

            if higher and not lower:
                pi, pv, pdir = i, row.high, +1
            if lower and not higher:
                pi, pv, pdir = i, row.low, -1

        elif pdir > 0:
            higher = row.high / pv - 1 > 0
            lower = row.low / pv - 1 < -threshold / 100

            if higher:
                pi, pv, pdir = i, row.high, +1
            elif lower:
                index.append(pi)
                values.append(pv)
                pi, pv, pdir = i, row.low, -1

        elif pdir < 0:
            higher = row.high / pv - 1 > threshold / 100
            lower = row.low / pv - 1 < 0

            if lower:
                pi, pv, pdir = i, row.low, -1
            elif higher:
                index.append(pi)
                values.append(pv)
                pi, pv, pdir = i, row.high, +1

    index = prices.index[index]

    return pd.Series(values, index)


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

        series = calc_zigzag(prices, threshold=self.threshold)
        series = chart.slice(series)

        label = repr(self)

        xv, yv = series_xy(series)
        ax.plot(xv, yv, label=label, color=None)
