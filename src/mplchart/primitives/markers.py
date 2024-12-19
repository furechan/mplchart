"""Marker primitives (experimental)"""

import numpy as np

from ..model import Primitive

from matplotlib.collections import LineCollection


class Marker(Primitive):
    """Base class for flag based markers"""

    indicator = None
    expr = None

    def __init__(self, expr=None):
        self.expr = expr

    def __ror__(self, indicator):
        if not callable(indicator):
            raise ValueError(f"{indicator!r} not callable!")

        return self.clone(indicator=indicator)

    def process(self, prices):
        """adds indicator result and flag to prices"""

        data = self.calc_result(prices, self.indicator)
        prices = prices.join(data)

        flag = np.where(prices.eval(self.expr) > 0.0, 1.0, 0.0)
        prices = prices.assign(flag=flag)

        return prices


class CrossMarker(Marker):
    """Cross Marker Primitive"""

    COLORENTRY = "green"
    COLOREXIT = "red"

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.main_axes()

        data = self.process(prices)
        data = chart.extract_df(data)

        mask = data.flag.diff().fillna(0).ne(0)

        xv = data.index[mask]
        yv = data.close[mask]
        flag = data.flag[mask]

        colorn = self.COLORENTRY
        colorx = self.COLOREXIT

        cv = np.where(flag > 0, colorn, colorx)

        ax.scatter(xv, yv, c=cv, s=12 * 12, alpha=0.6, marker=".")

        points = np.array([xv, yv]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        pos_color = (0.0, 0.0, 0.0, 1.0)
        neg_color = (0.0, 0.0, 0.0, 0.0)

        colors = [
            pos_color if flag.iloc[i] else neg_color for i in range(len(segments))
        ]

        lc = LineCollection(segments, colors=colors, linestyles="solid", linewidths=1.0)

        ax.add_collection(lc)

