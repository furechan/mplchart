"""Stripes primitive"""

import numpy as np

from ..model import Primitive
from ..utils import dataframe_eval


class Stripes(Primitive):
    """Stripes primitive.

    Shades vertical bands across all chart panes (using the root axes) during
    periods when a condition is active. The condition is derived from an
    indicator result or an expression. Use the ``|`` operator to attach to an
    indicator.

    Args:
        expr (str or pl.Expr, optional): Expression applied to the indicator
            result to produce a boolean/numeric signal. String expressions work
            for both pandas (``df.eval``) and polars (``df.sql``). Omit if the
            indicator itself already returns the signal.
        color (str, optional): Fill color for the shaded regions.
        alpha (float, optional): Opacity of the shaded regions, between 0.0
            and 1.0.

    Examples:
        RSI(14) | Stripes(expr="rsi < 30", color="green", alpha=0.15)
    """

    indicator = None

    def __init__(self, expr=None, *, color=None, alpha=None):
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

        if self.expr is not None:
            signal = dataframe_eval(result, self.expr)
        else:
            signal = result

        window = chart.mapper.calc_window()
        chart.window = window
        rownum = chart.mapper.rownum

        values = np.asarray(signal)[window]

        if not len(values):
            return

        # clip to 0/1 and forward-fill NaNs
        flag = np.clip(np.sign(values.astype(float)), 0.0, 1.0)
        nan_mask = np.isnan(flag)
        if nan_mask.any():
            idx = np.where(~nan_mask, np.arange(len(flag)), 0)
            np.maximum.accumulate(idx, out=idx)
            flag = flag[idx]

        # find contiguous on-regions via diff
        padded = np.concatenate([[0.0], flag, [0.0]])
        diff = np.diff(padded)
        starts = np.where(diff > 0)[0]
        ends = np.where(diff < 0)[0]

        color = self.color
        alpha = self.alpha

        lo = window.start
        for s, e in zip(starts, ends):
            x1 = rownum[lo + s]
            x2 = rownum[lo + e - 1]
            ax.axvspan(x1, x2, color=color, alpha=alpha)
