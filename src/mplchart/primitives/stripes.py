"""Marker primitives (experimental)"""

import numpy as np

from ..model import Primitive



class Stripes(Primitive):
    """Stripes primitive.

    Shades vertical bands across all chart panes (using the root axes) during
    periods when a condition is active. The condition is derived from an
    indicator result or a pandas ``eval`` expression. Use the ``|`` operator to
    attach to an indicator.

    Args:
        expr (str, optional): A pandas ``eval`` expression applied to the
            indicator result to produce a boolean/numeric signal. Omit if the
            indicator itself already returns the signal.
        color (str, optional): Fill color for the shaded regions.
        alpha (float, optional): Opacity of the shaded regions, between 0.0
            and 1.0.

    Examples:
        RSI(14) | Stripes(expr="rsi < 30", color="green", alpha=0.15)
    """

    indicator = None

    def __init__(self, expr: str | None = None, *, color: str | None = None, alpha: float | None = None):
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

