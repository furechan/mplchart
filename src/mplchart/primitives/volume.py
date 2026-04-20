"""Volume primitive"""

import numpy as np

from ..model import Primitive
from ..colors import closest_color
from ..utils import col_to_numpy


class Volume(Primitive):
    """Volume primitive.

    Plots volume bars colored by price direction (green for up-bars, red for
    down-bars). Rendered as a twinx overlay on the main pane so it does not
    affect the price axis. An optional SMA of volume can be overlaid.

    Args:
        sma (int, optional): Period for the volume SMA overlay. Omit to skip
            the moving average line.
        width (float): Width of each volume bar as a fraction of bar spacing.
            Defaults to 0.8.
        alpha (float): Opacity of the bars, between 0.0 and 1.0. Defaults to 0.5.
        colorup (str, optional): Color for bars where price closed up.
            Defaults to green.
        colordn (str, optional): Color for bars where price closed down.
            Defaults to red.
        colorma (str, optional): Color for the SMA overlay line.
            Defaults to gray.
    """

    def __init__(
        self,
        sma: int | None = None,
        *,
        width: float = 0.8,
        alpha: float = 0.5,
        colorup: str | None = None,
        colordn: str | None = None,
        colorma: str | None = None,
    ):
        self.sma = sma
        self.width = width
        self.alpha = alpha
        self.colorup = colorup
        self.colordn = colordn
        self.colorma = colorma

    def __str__(self):
        return self.__class__.__name__

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.get_axes("twinx")

        prices = chart.slice(prices, xcol="xloc")
        volume = np.asarray(col_to_numpy(prices, "volume"))
        close = np.asarray(col_to_numpy(prices, "close"))

        with np.errstate(invalid="ignore"):
            change = np.diff(close, prepend=np.nan) / np.roll(close, 1)
            change[0] = np.nan

        xv = np.asarray(prices["xloc"])

        width = self.width
        alpha = self.alpha
        colorup = closest_color(self.colorup or "green")
        colordn = closest_color(self.colordn or "red")
        colorma = closest_color(self.colorma or "gray")

        color = np.where(change > 0, colorup, colordn)

        if ax._label == "twinx":
            vmax = volume.max()
            ax.set_ylim(0.0, vmax * 4.0)
            ax.yaxis.set_visible(False)

        ax.bar(xv, volume, width=width, alpha=alpha, color=color)

        if self.sma:
            n = self.sma
            valid = np.convolve(volume, np.ones(n) / n, mode="valid")
            average = np.concatenate([np.full(n - 1, np.nan), valid])
            ax.plot(xv, average, linewidth=0.7, alpha=alpha, color=colorma)
