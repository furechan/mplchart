"""Volume primitive"""

import numpy as np
import pandas as pd

from ..model import Primitive
from ..colors import closest_color


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

    def process(self, prices):
        volume = prices.volume
        change = prices.close.pct_change()

        result = dict(volume=volume, change=change)

        if self.sma:
            result["average"] = volume.rolling(self.sma).mean()

        result = pd.DataFrame(result)

        return result

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.get_axes("twinx")

        data = self.process(prices)
        data = chart.slice(data)    

        index = data.index
        volume = data.volume
        change = data.change

        width = self.width
        alpha = self.alpha
        colorup = closest_color("green")
        colordn = closest_color("red")
        colorma = closest_color("gray")

        color = np.where(change > 0, colorup, colordn)

        # ax.set_zorder(0)

        # This should always be the case !?
        if ax._label == "twinx":
            vmax = data.volume.max()
            ax.set_ylim(0.0, vmax * 4.0)
            ax.yaxis.set_visible(False)

        ax.bar(index, volume, width=width, alpha=alpha, color=color)

        if self.sma:
            average = data.average
            ax.plot(index, average, linewidth=0.7, alpha=alpha, color=colorma)
