"""ZigZag Primitive"""

import pandas as pd
from ..model import Primitive
from ..utils import series_xy


def calc_zigzag(prices, threshold=5.0):
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
    same_scale = True

    def __init__(self, threshold=5.0):
        self.threshold = threshold

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            target = chart.get_target(self)
            ax = chart.get_axes(target)

        series = calc_zigzag(prices, threshold=self.threshold)
        series = chart.slice(series)

        label = repr(self)

        xv, yv = series_xy(series)
        ax.plot(xv, yv, label=label, color=None)
