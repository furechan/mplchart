""" Markers """

import numpy as np

from ..model import Primitive

from matplotlib.collections import LineCollection


class TradeMarker(Primitive):
    """ Trade Marker Primitive """

    candidate_items = ('pos', 'macdhist', 'ppohist')
    show_labels = False
    indicator = None

    def __init__(self, *, bands=True, lines=True):
        self.bands = bands
        self.lines = lines

    def __ror__(self, indicator):
        if not callable(indicator):
            raise ValueError(f"{indicator!r} not callable!")

        return self.clone(indicator=indicator)

    def process(self, prices, indicator=None):
        """ adds indicator result and position to prices """

        if indicator:
            data = indicator(prices)
            prices = prices.join(data)

        items = [c for c in prices.columns if c in self.candidate_items]
        if not items:
            raise ValueError("No valid pos column!")

        item = items[0]
        pos = np.where(prices[item] > 0.0, 1.0, 0.0)
        prices = prices.assign(pos=pos)

        return prices

    def plot_markers(self, data, ax):
        """ plots markers (post process) """

        mask = data.pos.diff().fillna(0).ne(0)

        xv = data.index[mask]
        yv = data.close[mask]
        pos = data.pos[mask]

        cv = np.where(pos > 0, 'g', 'r')

        ax.scatter(xv, yv, c=cv, s=12 * 12, alpha=0.6, marker=".")

    def plot_lines(self, data, ax):
        """ plots lines (post process) """

        mask = data.pos.diff().fillna(0).ne(0)

        xv = data.index[mask]
        yv = data.close[mask]
        pos = data.pos[mask]

        points = np.array([xv, yv]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        pos_color = (0.0, 0.0, 0.0, 1.0)
        neg_color = (0.0, 0.0, 0.0, 0.0)

        colors = [pos_color if pos.iloc[i] else neg_color for i in range(len(segments))]

        lc = LineCollection(segments, colors=colors, linestyles='solid', linewidths=1.0)

        ax.add_collection(lc)

    def plot_labels(self, data, ax):
        """ plots labels (post process) """

        mask = data.pos.diff().fillna(0).ne(0)

        xv = data.index[mask]
        yv = data.close[mask]
        pos = data.pos[mask]
        rv = yv.pct_change()

        text_style = dict(horizontalalignment='left', verticalalignment='bottom',
                          fontsize=12, fontfamily='monospace')

        for i in range(yv.size):
            if pos[i] <= 0:
                x, y, r = xv[i], yv.iloc[i], rv.iloc[i]
                s = "{:.2%}".format(r)
                ax.text(x, y, s, **text_style)

    def plot_vline(self, data, ax):
        """ plots labels (post process) """

        mask = data.pos.diff().fillna(0).ne(0)

        xv = data.index[mask]
        pv = data.pos[mask]

        for x, p in zip(xv, pv):
            color = 'g' if p > 0 else 'r'
            ax.axvline(x, color=color, linestyle='solid', linewidth=0.5, alpha=0.5)

    def plot_vspan(self, data, ax):
        """ plots labels (post process) """

        mask = data.pos.diff().fillna(0).ne(0)
        color = 'green'
        alpha = 0.1

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

    def plot_handler(self, data, chart, ax=None):
        """ main plot handler from raw prices """

        if ax is None:
            ax = chart.main_axes()

        indicator = self.indicator or chart.last_indicator

        data = self.process(data, indicator=indicator)
        data = chart.extract_df(data)

        self.plot_markers(data, ax)

        if self.lines:
            self.plot_lines(data, ax)

        if self.bands:
            ax = chart.root_axes()
            self.plot_vspan(data, ax)


class BaseMarker(Primitive):
    candidate_items = ('pos', 'macdhist', 'ppohist')
    indicator = None

    def __ror__(self, indicator):
        if not callable(indicator):
            raise ValueError(f"{indicator!r} not callable!")

        return self.clone(indicator=indicator)

    def process(self, prices, indicator=None):
        """ adds indicator result and position to prices """

        if indicator:
            data = indicator(prices)
            prices = prices.join(data)

        items = [c for c in prices.columns if c in self.candidate_items]
        if not items:
            raise ValueError("No valid pos column!")

        item = items[0]
        pos = np.where(prices[item] > 0.0, 1.0, 0.0)
        prices = prices.assign(pos=pos)

        return prices


class TradeBands(BaseMarker):
    """ Trade Marker Primitive """

    def plot_handler(self, data, chart, ax=None):
        """ main plot handler from raw prices """

        if ax is None:
            ax = chart.root_axes()

        indicator = self.indicator or chart.last_indicator

        data = self.process(data, indicator=indicator)
        data = chart.extract_df(data)

        mask = data.pos.diff().fillna(0).ne(0)
        color = 'green'
        alpha = 0.1

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
