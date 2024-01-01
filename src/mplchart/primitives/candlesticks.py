""" Candlesticks primitive """

import numpy as np

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from matplotlib.collections import PolyCollection

from ..model import Primitive

import warnings


class Candlesticks(Primitive):
    """
    Candlesticks Primitive

    Used to plot prices as candlesticks
    """

    WIDTH = 0.8
    COLORUP = "black"
    COLORDN = "black"
    COLOROFF = "white"
    USE_BARS = False

    def __init__(self, use_bars=USE_BARS):
        self.use_bars = use_bars

    def __str__(self):
        return self.__class__.__name__

    def plot_handler(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        label = str(self)
        data = chart.extract_df(data)

        width = chart.get_setting("candles", "width", self.WIDTH)
        colorup = chart.get_setting("candles.up", "color", self.COLORUP)
        colordn = chart.get_setting("candles.dn", "color", self.COLORDN)
        coloroff = chart.get_setting("candles.off", "color", self.COLOROFF)

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


def plot_csbars(
    data, ax=None, width=0.6, colorup="k", colordn="k", coloroff="w", label=None
):
    """plots candlesticks as bars"""

    ax = ax or plt.gca()

    xvalues = data.index.values

    high, low = data.high, data.low
    change = data.close.pct_change()
    filled = data.close <= data.open
    upper = np.maximum(data.open, data.close)
    lower = np.minimum(data.open, data.close)

    with np.errstate(invalid="ignore"):
        color = np.where(change < 0.0, colordn, colorup)
        edgecolor = np.where(change < 0.0, colordn, colorup)
        fillcolor = np.where(filled, color, coloroff)

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
        color=fillcolor,
        edgecolor=edgecolor,
        width=width,
        fill=True,
        linewidth=0.7,
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
    filled = data.close <= data.open
    upper = np.maximum(data.open, data.close)
    lower = np.minimum(data.open, data.close)

    if count > 0:
        # spacing = (xvalues[-1] - xvalues[0]) / (count - 1)
        spacing = np.nanmin(np.diff(xvalues))
    else:
        spacing = 1.0

    half_bar = spacing * width / 2.0

    with np.errstate(invalid="ignore"):
        edgecolor = np.where(change < 0.0, colordn, colorup)
        facecolor = np.where(filled, edgecolor, coloroff)

    verts = [
        (
            (x - half_bar, b),
            (x - half_bar, t),
            (x, t),
            (x, h),
            (x, t),
            (x + half_bar, t),
            (x + half_bar, b),
            (x, b),
            (x, l),
            (x, b),
        )
        for x, b, t, l, h in zip(xvalues, lower, upper, low, high)
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
