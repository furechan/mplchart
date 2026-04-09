"""Candlesticks primitive"""

import numpy as np

import matplotlib.pyplot as plt

from matplotlib.collections import PolyCollection

from ..model import Primitive
from ..utils import col_to_numpy


class Candlesticks(Primitive):
    """Candlesticks primitive.

    Plots OHLC prices as candlestick chart. Up-bars (close ≥ open) are drawn
    hollow (fill matches the background); down-bars (close < open) are filled.

    Args:
        width (float): Width of each candlestick body as a fraction of bar
            spacing. Defaults to 0.8.
        alpha (float): Opacity of the candlesticks, between 0.0 and 1.0.
            Defaults to 1.0.
        colorup (str, optional): Color for up-bars. Defaults to the current
            ``text.color`` matplotlib parameter.
        colordn (str, optional): Color for down-bars. Defaults to the current
            ``text.color`` matplotlib parameter.
        use_bars (bool): If ``True``, render using bar charts instead of
            polygons. Defaults to ``False``.
    """

    def __init__(
        self,
        *,
        width: float = 0.8,
        alpha: float = 1.0,
        colorup: str | None = None,
        colordn: str | None = None,
        use_bars: bool = False,
    ):
        self.width = width
        self.alpha = alpha
        self.colorup = colorup
        self.colordn = colordn
        self.use_bars = use_bars

    def __str__(self):
        return self.__class__.__name__

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        window = chart.mapper.calc_window()
        xvalues = chart.mapper.rownum[window]
        dwindow = chart.mapper.data_window(window)
        prices = chart.slice(prices) if hasattr(prices, "index") else prices[dwindow]

        label = str(self)
        width = self.width
        alpha = self.alpha

        edgecolor = plt.rcParams["text.color"]
        facecolor = plt.rcParams["axes.facecolor"]

        colorup = self.colorup or edgecolor
        colordn = self.colordn or edgecolor
        coloroff = self.colorup or facecolor

        if self.use_bars:
            return plot_csbars(prices, xvalues, ax=ax, width=width, alpha=alpha, colorup=colorup, colordn=colordn, coloroff=coloroff, label=label)
        else:
            return plot_cspoly(prices, xvalues, ax=ax, width=width, alpha=alpha, colorup=colorup, colordn=colordn, coloroff=coloroff, label=label)


def plot_cspoly(
    data, xvalues, *, ax=None, width=0.6, alpha=0.2, colorup=None, colordn=None, coloroff=None, label=None
):
    """plots candlesticks as polygons"""

    ax = ax or plt.gca()

    textcolor = plt.rcParams["text.color"]
    facecolor_ = plt.rcParams["axes.facecolor"]
    colorup = colorup or textcolor
    colordn = colordn or textcolor
    coloroff = coloroff or facecolor_

    high   = col_to_numpy(data, "high")
    low    = col_to_numpy(data, "low")
    open_  = col_to_numpy(data, "open")
    close  = col_to_numpy(data, "close")

    change = np.diff(close, prepend=np.nan) / close
    bottom = np.minimum(open_, close)
    top    = np.maximum(open_, close)

    count = len(xvalues)

    if count > 0:
        spacing = np.nanmin(np.diff(xvalues)) if count > 1 else 1.0
    else:
        spacing = 1.0

    half_bar = spacing * width / 2.0

    with np.errstate(invalid="ignore"):
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

    linewidths = (0.7,)

    poly = PolyCollection(
        verts,
        alpha=alpha,
        facecolors=facecolor,
        edgecolors=edgecolor,
        linewidths=linewidths,
        label=label,
    )

    ax.add_collection(poly)
    ax.autoscale_view()


def plot_csbars(
    data, xvalues, *, ax=None, width=0.6, alpha=0.2, colorup=None, colordn=None, coloroff=None, label=None
):
    """plots candlesticks as bars"""

    ax = ax or plt.gca()

    textcolor = plt.rcParams["text.color"]
    facecolor_ = plt.rcParams["axes.facecolor"]
    colorup = colorup or textcolor
    colordn = colordn or textcolor
    coloroff = coloroff or facecolor_

    high   = col_to_numpy(data, "high")
    low    = col_to_numpy(data, "low")
    open_  = col_to_numpy(data, "open")
    close  = col_to_numpy(data, "close")

    change = np.diff(close, prepend=np.nan) / close
    upper  = np.maximum(open_, close)
    lower  = np.minimum(open_, close)

    with np.errstate(invalid="ignore"):
        edgecolor = np.where(change >= 0.0, colorup, colordn)
        facecolor = np.where(change >= 0.0, coloroff, colordn)

    ax.bar(
        xvalues,
        height=high - low,
        bottom=low,
        edgecolor=edgecolor,
        width=0.0,
        alpha=alpha,
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
        alpha=alpha,
        fill=True,
        linewidth=0.7,
    )
