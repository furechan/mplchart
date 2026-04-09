"""Markers primitive"""

import numpy as np

from ..model import Primitive
from ..utils import dataframe_eval, col_to_numpy


class Markers(Primitive):
    """Markers primitive.

    Plots scatter markers on the main pane at the close price whenever a
    condition changes. The condition is evaluated from an indicator result or
    an expression. Use the ``|`` operator to attach to an indicator.

    Args:
        expr (str or pl.Expr, optional): Expression applied to the indicator
            result to produce a boolean/numeric signal. String expressions work
            for both pandas (``df.eval``) and polars (``df.sql``). Omit if the
            indicator itself already returns the signal.
        color (str or list of str, optional): Marker color. Pass a two-element
            list ``[color_off, color_on]`` to use different colors for signal
            transitions. Defaults to the matplotlib default color cycle.
        marker (str): Matplotlib marker symbol. Defaults to ``"."``.
        alpha (float): Opacity of the markers, between 0.0 and 1.0.
            Defaults to 0.6.

    Examples:
        RSI(14) | Markers(expr="rsi < 30", color=["gray", "green"])
    """

    indicator = None

    def __init__(
        self,
        expr=None,
        *,
        color=None,
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
            signal = dataframe_eval(result, self.expr)
        else:
            signal = result

        window = chart.mapper.calc_window()
        chart.window = window
        rownum = chart.mapper.rownum

        flag = np.clip(np.sign(np.asarray(signal, dtype=float)), 0, 1)
        close = np.asarray(col_to_numpy(prices, "close"), dtype=float)

        # apply window
        flag = flag[window]
        close = close[window]

        # forward-fill NaNs in flag
        nan_mask = np.isnan(flag)
        if nan_mask.any():
            idx = np.where(~nan_mask, np.arange(len(flag)), 0)
            np.maximum.accumulate(idx, out=idx)
            flag = flag[idx]

        # find positions where flag changes
        diff = np.diff(flag, prepend=np.nan)
        mask = ~np.isnan(diff) & (diff != 0)

        if not mask.sum():
            return

        xv = rownum[window.start + np.where(mask)[0]]
        yv = close[mask]
        flag_at = flag[mask]

        marker = self.marker
        color = self.color
        alpha = self.alpha

        if isinstance(color, list):
            color = np.where(flag_at > 0, color[1], color[0])

        ax.scatter(xv, yv, c=color, s=12 * 12, alpha=alpha, marker=marker)
