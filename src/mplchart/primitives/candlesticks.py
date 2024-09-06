""" Candlesticks primitive """

import warnings

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from matplotlib.collections import PolyCollection

from ..model import Primitive



class Candlesticks(Primitive):
    """
    Candlesticks Primitive

    Used to plot prices as candlesticks
    """

    def __init__(self, *, width: float = 0.8, colorup: str = None, colordn: str = None, use_bars: bool = False):
        self.width = width
        self.colorup = colorup
        self.colordn = colordn
        self.use_bars = use_bars

    def __str__(self):
        return self.__class__.__name__

    def plot_handler(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        label = str(self)
        data = chart.extract_df(data)

        width = self.width

        colorup = self.colorup or "k"
        colordn = self.colordn or "k"
        coloroff = self.colorup or "w"

        if self.use_bars:
            return plot_csbars(
                data=data,
                ax=ax,
                width=width,
                colorup=colorup,
                colordn=colordn,
                coloroff=coloroff,
                label=label,
            )
        else:
            return plot_cspoly(
                data=data,
                ax=ax,
                width=width,
                colorup=colorup,
                colordn=colordn,
                coloroff=coloroff,
                label=label,
            )


def plot_cspoly(
        data, ax=None, width=0.6, colorup="k", colordn="k", coloroff="w", label=None
):
    """plots candlesticks as polygons"""

    ax = ax or plt.gca()

    count = len(data)

    xvalues = data.index.values

    if np.issubdtype(xvalues.dtype, np.datetime64):
        warnings.warn("plot_cspoly forced to convert dates!")
        xvalues = mdates.date2num(xvalues)

    high, low = data.high, data.low
    change = data.close.pct_change()
    bottom = np.minimum(data.open, data.close)
    top = np.maximum(data.open, data.close)

    if count > 0:
        spacing = np.nanmin(np.diff(xvalues))
    else:
        spacing = 1.0

    half_bar = spacing * width / 2.0

    with np.errstate(invalid="ignore"):
        # edgecolor = np.where(change < 0.0, colordn, colorup)
        # facecolor = np.where(filled, edgecolor, coloroff)
        edgecolor = np.where(change >= 0.0, colorup, colordn)
        facecolor = np.where(change >= 0.0, coloroff, colordn)

    verts = [
        (
            (xv - half_bar, bt),
            (xv - half_bar, tp),
            (xv, tp),
            (xv, hi),
            (xv, tp),
            (xv + half_bar, tp),
            (xv + half_bar, bt),
            (xv, bt),
            (xv, lo),
            (xv, bt),
        )
        for xv, bt, tp, lo, hi in zip(xvalues, bottom, top, low, high)
    ]

    verts = np.asarray(verts)

    linewidths = (0.7,)

    poly = PolyCollection(
        verts,
        facecolors=facecolor,
        edgecolors=edgecolor,
        linewidths=linewidths,
        label=label,
    )

    ax.add_collection(poly)
    ax.autoscale_view()


def plot_csbars(
        data, ax=None, width=0.6, colorup="k", colordn="k", coloroff="w", label=None
):
    """plots candlesticks as bars"""

    ax = ax or plt.gca()

    xvalues = data.index.values

    high, low = data.high, data.low
    change = data.close.pct_change()
    upper = np.maximum(data.open, data.close)
    lower = np.minimum(data.open, data.close)

    with np.errstate(invalid="ignore"):
        edgecolor = np.where(change >= 0.0, colorup, colordn)
        facecolor = np.where(change >= 0.0, coloroff, colordn)

    ax.bar(
        xvalues,
        height=high - low,
        bottom=low,
        edgecolor=edgecolor,
        width=0.0,
        linewidth=0.7,
        label=label,
    )
    ax.bar(
        xvalues,
        height=upper - lower,
        bottom=lower,
        color=facecolor,
        edgecolor=edgecolor,
        width=width,
        fill=True,
        linewidth=0.7,
    )
