"""Marker primitives (experimental)"""

import numpy as np

from ..model import Primitive



class Stripes(Primitive):
    """Stripes Primitive"""

    indicator = None

    def __init__(self, expr: str = None, *, color: str = None, alpha: float = None):
        self.expr = expr
        self.color = color
        self.alpha = alpha

    def __ror__(self, indicator):
        if not callable(indicator):
            raise ValueError(f"{indicator!r} not callable!")

        return self.clone(indicator=indicator)

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.root_axes()

        result = chart.calc_result(prices, self.indicator)
        result = chart.slice(result)

        if not len(result):
            return

        if self.expr:
            result = result.eval(self.expr)

        flag = np.clip(np.sign(result), 0.0, 1.0).ffill()
        csum = flag.diff().fillna(0).ne(0).cumsum()
        aggs = flag[flag >0].index.to_series().groupby(csum).agg(['first', 'last'])

        color = self.color
        alpha = self.alpha

        for x1, x2 in aggs.itertuples(index=False, name=None):
            ax.axvspan(x1, x2, color=color, alpha=alpha)

