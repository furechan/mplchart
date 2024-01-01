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

    WIDTH = 0.8
    COLORUP = "black"
    COLORDN = "red"

    def __str__(self):
        return self.__class__.__name__

    def plot_handler(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        label = str(self)
        data = chart.extract_df(data)

        width = chart.get_setting("ohlc.", "width", self.WIDTH)
        colorup = chart.get_setting("ohlc.up", "color", self.COLORUP)
        colordn = chart.get_setting("ohlc.dn", "color", self.COLORDN)

        return plot_ohlc(
            data=data, ax=ax, width=width, colorup=colorup, colordn=colordn, label=label
        )


def plot_ohlc(data, ax=None, width=0.8, colorup="k", colordn="k", label=None):
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
            (x, l),
            (x, o),
            (x - half_bar, o),
            (x, o),
            (x, c),
            (x + half_bar, c),
            (x, c),
            (x, h),
        )
        for x, o, h, l, c in zip(xvalues, data.open, data.high, data.low, data.close)
    ]

    verts = np.asarray(verts)

    linewidths = (1.0,)

    poly = PolyCollection(
        verts, edgecolors=edgecolor, linewidths=linewidths, label=label
    )

    ax.add_collection(poly)
    ax.autoscale_view()
