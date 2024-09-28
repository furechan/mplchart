"""Volume primitive"""

import numpy as np
import pandas as pd

from ..model import Primitive
from ..colors import closest_color


class Volume(Primitive):
    """
    Volume Primitive

    Used to plot the volume

    Args:
        sma (int) : the period of the simple moving average, optional
    """

    def __init__(
        self,
        sma: int = None,
        *,
        width: float = 0.8,
        colorup: str = None,
        colordn: str = None,
        colorma: str = None,
    ):
        self.sma = sma
        self.width = width
        self.colorup = colorup
        self.colordn = colordn
        self.colorma = colorma

    def __str__(self):
        return self.__class__.__name__

    def calc(self, data):
        volume = data.volume
        change = data.close.pct_change()

        result = dict(volume=volume, change=change)

        if self.sma:
            result["average"] = volume.rolling(self.sma).mean()

        result = pd.DataFrame(result)

        return result

    def plot_handler(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes("twinx")

        data = self.calc(data)
        data = chart.extract_df(data)

        index = data.index
        volume = data.volume
        change = data.change

        width = self.width
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

        ax.bar(index, volume, width=width, alpha=0.3, color=color)

        if self.sma:
            average = data.average
            ax.plot(index, average, linewidth=0.7, color=colorma)
