"""Marker primitives (experimental)"""

import numpy as np

from ..model import Primitive


class Markers(Primitive):
    """Marker Primitive"""

    indicator = None

    def __init__(
        self,
        expr: str = None,
        *,
        color: str = None,
        marker: str = ".",
        alpha: float = 0.6,
    ):
        self.expr = expr
        self.color = color
        self.marker = marker
        self.alpha = alpha

    def __ror__(self, indicator):
        if not callable(indicator):
            raise ValueError(f"{indicator!r} not callable!")

        return self.clone(indicator=indicator)

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.main_axes()

        result = chart.calc_result(prices, self.indicator)

        if self.expr is not None:
            result = result.eval(self.expr)

        flag = np.clip(np.sign(result), 0, 1)

        result = prices.assign(flag=flag)

        result = chart.slice(result)

        mask = result.flag.ffill().diff().fillna(0).ne(0)

        if not mask.sum():
            return

        result = result[mask]

        xv = result.index
        yv = result.close
        flag = result.flag

        marker = self.marker
        color = self.color
        alpha = self.alpha

        if isinstance(self.color, list):
            color = np.where(flag > 0, color[1], color[0])

        ax.scatter(xv, yv, c=color, s=12 * 12, alpha=alpha, marker=marker)
