"""OHLC primitive

Style settings consumed by this primitive:

    ohlc.up.color    up-bars, close ≥ previous close (default: text.color)
    ohlc.down.color  down-bars (default: text.color)
    ohlc.alpha       opacity (default: 1.0)

Each kwarg overrides its own setting per side (kwarg → setting →
``text.color``) — the side colors are independent params, not an atomic
scheme; an explicit ``alpha=`` kwarg wins over ``ohlc.alpha``.
"""

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
        alpha (float, optional): Opacity of the bars, between 0.0 and 1.0.
            Defaults to the ``ohlc.alpha`` setting, else 1.0.
        colorup (str, optional): Color for up-bars (close ≥ previous close).
            Defaults to the ``ohlc.up.color`` setting, else ``text.color``.
        colordn (str, optional): Color for down-bars. Defaults to the
            ``ohlc.down.color`` setting, else ``text.color``.
    """

    def __init__(self, *, width: float = 0.8, alpha: float | None = None, colorup: str | None = None, colordn: str | None = None):
        self.width = width
        self.alpha = alpha
        self.colorup = colorup
        self.colordn = colordn

    def __str__(self):
        return self.__class__.__name__

    def apply_to_chart(self, chart):
        ax = chart.canvas.get_axes()

        prices = chart.view.slice(chart.view.prices, xcol="xloc")
        xvalues = col_to_numpy(prices, "xloc")
        open_ = col_to_numpy(prices, "open")
        high = col_to_numpy(prices, "high")
        low = col_to_numpy(prices, "low")
        close = col_to_numpy(prices, "close")

        textcolor = plt.rcParams["text.color"]

        label = str(self)
        width = self.width

        alpha = chart.canvas.get_setting("ohlc", "alpha", ax, override=self.alpha, fallback=1.0)

        # per-side chain: kwarg → setting → textcolor. The two side colors are
        # independent params, not an atomic scheme (unlike candlesticks —
        # there is no coordinated look to protect here)
        resolve = chart.canvas.resolve_color
        colorup = resolve("ohlc.up", ax, override=self.colorup, fallback=textcolor)
        colordn = resolve("ohlc.down", ax, override=self.colordn, fallback=textcolor)

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

    textcolor = plt.rcParams["text.color"]
    colorup = colorup or textcolor
    colordn = colordn or textcolor
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
