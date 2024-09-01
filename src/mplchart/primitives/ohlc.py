""" OHLC primitive """

import numpy as np

import matplotlib.pyplot as plt

from matplotlib.collections import PolyCollection

from ..model import Primitive


class OHLC(Primitive):
    """
    Open High Low Close Primitive

    Used to plot prices as OHLC bars
    """

    def __init__(self, *, width: float = 0.8, colorup: str = None, colordn: str = None):
        self.width = width
        self.colorup = colorup
        self.colordn = colordn

    def __str__(self):
        return self.__class__.__name__

    def plot_handler(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        label = str(self)
        data = chart.extract_df(data)

        width = self.width
        colorup = self.colorup or "k"
        colordn = self.colordn or "r"

        return plot_ohlc(
            data=data, ax=ax, width=width, colorup=colorup, colordn=colordn, label=label
        )


def plot_ohlc(data, ax=None, width=0.8, colorup="k", colordn="r", label=None):
    """plots open-high-low-close charts as polygons"""

    ax = ax or plt.gca()

    count = len(data)

    xvalues = data.index
    change = data.close.pct_change()

    if count > 0:
        avg_spacing = (xvalues[-1] - xvalues[0]) / (count - 1)
    else:
        avg_spacing = 1.0

    half_bar = avg_spacing * width / 2.0

    with np.errstate(invalid="ignore"):
        edgecolor = np.where(change < 0.0, colordn, colorup)

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
        for xv, op, hi, lo, cl in zip(xvalues, data.open, data.high, data.low, data.close)
    ]

    verts = np.asarray(verts)

    linewidths = (1.0,)

    poly = PolyCollection(
        verts, edgecolors=edgecolor, linewidths=linewidths, label=label
    )

    ax.add_collection(poly)
    ax.autoscale_view()
