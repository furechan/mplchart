""" Markers """

import numpy as np

from ..model import Primitive

from matplotlib.collections import LineCollection


class PosMarker(Primitive):
    """Base class for position based markers"""

    candidate_items = ("pos", "macdhist", "ppohist")
    indicator = None
    expr = None

    def __init__(self, expr=None):
        self.expr = expr

    def __ror__(self, indicator):
        if not callable(indicator):
            raise ValueError(f"{indicator!r} not callable!")

        return self.clone(indicator=indicator)

    def default_item(self, prices):
        items = [c for c in prices.columns if c in self.candidate_items]
        if items:
            return items[0]
        else:
            raise ValueError("No valid position column!")

    def process(self, prices, chart):
        """adds indicator result and position to prices"""

        indicator = self.indicator or chart.last_indicator

        if indicator:
            data = indicator(prices)
            prices = prices.join(data)

        expr = self.expr or self.default_item(prices)
        pos = np.where(prices.eval(expr) > 0.0, 1.0, 0.0)
        prices = prices.assign(pos=pos)

        return prices


class TradeMarker(PosMarker):
    """Trade Marker Primitive"""

    COLORENTRY = "green"
    COLOREXIT = "red"

    def plot_handler(self, data, chart, ax=None):
        """main plot handler from raw prices"""

        if ax is None:
            ax = chart.main_axes()

        data = self.process(data, chart)
        data = chart.extract_df(data)

        mask = data.pos.diff().fillna(0).ne(0)

        xv = data.index[mask]
        yv = data.close[mask]
        pos = data.pos[mask]

        colorn = chart.get_setting("marker.entry", "color", self.COLORENTRY)
        colorx = chart.get_setting("merker.exit", "color", self.COLOREXIT)

        cv = np.where(pos > 0, colorn, colorx)

        ax.scatter(xv, yv, c=cv, s=12 * 12, alpha=0.6, marker=".")

        points = np.array([xv, yv]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        pos_color = (0.0, 0.0, 0.0, 1.0)
        neg_color = (0.0, 0.0, 0.0, 0.0)

        colors = [pos_color if pos.iloc[i] else neg_color for i in range(len(segments))]

        lc = LineCollection(segments, colors=colors, linestyles="solid", linewidths=1.0)

        ax.add_collection(lc)


class TradeSpan(PosMarker):
    """Trade Span Primitive"""

    COLOR = "green"
    ALPHA = 0.1

    def plot_handler(self, data, chart, ax=None):
        """main plot handler from raw prices"""

        if ax is None:
            ax = chart.root_axes()

        data = self.process(data, chart)
        data = chart.extract_df(data)
        pos = data.pos

        mask = pos.diff().fillna(0).ne(0)

        color = chart.get_setting("tradespan", "color", self.COLOR)
        alpha = self.ALPHA

        xv = data.index[mask]
        sv = data.pos[mask]
        x = s = px = None

        for x, s in zip(xv, sv):
            if s > 0 and px is None:
                px = x
            if s <= 0 and px is not None:
                ax.axvspan(px, x, color=color, alpha=alpha)
                px = None

        if s <= 0 and px is not None:
            ax.axvspan(px, x, color=color, alpha=alpha)
