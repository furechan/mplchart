"""OHLC primitive"""

import numpy as np

import matplotlib.pyplot as plt

from matplotlib.collections import PolyCollection

from ..model.primitive import Primitive
from ..utils import col_to_numpy, xvalues_to_float


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

    def apply_to_chart(self, chart):
        ax = chart.get_axes()

        prices = chart.slice(chart.prices, xcol="xloc")
        xvalues = np.asarray(prices["xloc"])
        open_ = np.asarray(col_to_numpy(prices, "open"))
        high = np.asarray(col_to_numpy(prices, "high"))
        low = np.asarray(col_to_numpy(prices, "low"))
        close = np.asarray(col_to_numpy(prices, "close"))

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

    # floats up front (datetime64 → date numbers) so spacing and verts share one scale
    xvalues = xvalues_to_float(xvalues)

    count = len(xvalues)

    if count > 1:
        avg_spacing = (xvalues[-1] - xvalues[0]) / (count - 1)
    else:
        avg_spacing = 1.0

    half_bar = avg_spacing * width / 2.0

    with np.errstate(invalid="ignore"):
        change = np.diff(close, prepend=np.nan) / np.roll(close, 1)
        edgecolors = np.where(change < 0.0, colordn, colorup)

    # (n, 8, 2) vertex array — a 3-D ndarray hits PolyCollection's set_verts fast path
    xv = xvalues
    kx = np.stack([xv, xv, xv - half_bar, xv, xv, xv + half_bar, xv, xv], axis=1)
    ky = np.stack([low, open_, open_, open_, close, close, close, high], axis=1)
    verts = np.stack([kx, ky], axis=2)

    poly = PolyCollection(
        verts,  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # stubs say Sequence[ArrayLike]; 3-D ndarray is supported
        edgecolors=edgecolors, linewidths=(1.0,), alpha=alpha, label=label
    )

    ax.add_collection(poly)
    ax.autoscale_view()
