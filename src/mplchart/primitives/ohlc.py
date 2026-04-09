"""OHLC primitive"""

import numpy as np

import matplotlib.pyplot as plt

from matplotlib.collections import PolyCollection

from ..model import Primitive
from ..utils import col_to_numpy


class OHLC(Primitive):
    """Open High Low Close primitive.

    Plots OHLC prices as traditional bar charts with horizontal tick marks for
    the open (left tick) and close (right tick) prices.

    Args:
        width (float): Width of each bar as a fraction of bar spacing.
            Defaults to 0.8.
        alpha (float): Opacity of the bars, between 0.0 and 1.0. Defaults to 1.0.
        colorup (str, optional): Color for up-bars (close ≥ previous close).
            Defaults to the current ``text.color`` matplotlib parameter.
        colordn (str, optional): Color for down-bars. Defaults to the current
            ``text.color`` matplotlib parameter.
    """

    def __init__(self, *, width: float = 0.8, alpha: float = 1.0, colorup: str | None = None, colordn: str | None = None):
        self.width = width
        self.alpha = alpha
        self.colorup = colorup
        self.colordn = colordn

    def __str__(self):
        return self.__class__.__name__

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        window = chart.mapper.calc_window()
        chart.window = window
        dwindow = chart.mapper.data_window(window)

        xvalues = chart.mapper.rownum[window]
        open_ = np.asarray(col_to_numpy(prices, "open"))[dwindow]
        high = np.asarray(col_to_numpy(prices, "high"))[dwindow]
        low = np.asarray(col_to_numpy(prices, "low"))[dwindow]
        close = np.asarray(col_to_numpy(prices, "close"))[dwindow]

        textcolor = plt.rcParams["text.color"]

        label = str(self)
        width = self.width
        alpha = self.alpha
        colorup = self.colorup or textcolor
        colordn = self.colordn or textcolor

        return plot_ohlc(
            xvalues=xvalues,
            open_=open_, high=high, low=low, close=close,
            ax=ax,
            width=width,
            alpha=alpha,
            colorup=colorup,
            colordn=colordn,
            label=label,
        )


def plot_ohlc(xvalues, open_, high, low, close, ax=None, width=0.8, alpha=1.0, colorup=None, colordn=None, label=None):
    """Plot open-high-low-close charts as polygons."""

    edgecolor = plt.rcParams["text.color"]
    colorup = colorup or edgecolor
    colordn = colordn or edgecolor
    ax = ax or plt.gca()

    count = len(xvalues)

    if count > 1:
        avg_spacing = (xvalues[-1] - xvalues[0]) / (count - 1)
    else:
        avg_spacing = 1.0

    half_bar = avg_spacing * width / 2.0

    with np.errstate(invalid="ignore"):
        change = np.diff(close, prepend=np.nan) / np.roll(close, 1)
        edgecolors = np.where(change < 0.0, colordn, colorup)

    verts = [
        (
            (xv, lo),
            (xv, op),
            (xv - half_bar, op),
            (xv, op),
            (xv, cl),
            (xv + half_bar, cl),
            (xv, cl),
            (xv, hi),
        )
        for xv, op, hi, lo, cl in zip(xvalues, open_, high, low, close)
    ]

    poly = PolyCollection(
        verts, edgecolors=edgecolors, linewidths=(1.0,), alpha=alpha, label=label
    )

    ax.add_collection(poly)
    ax.autoscale_view()
