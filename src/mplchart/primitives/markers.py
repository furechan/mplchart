"""Marker primitives (experimental)"""

import numpy as np

from ..model import Primitive


class Markers(Primitive):
    """Markers primitive.

    Plots scatter markers on the main pane at the close price whenever a
    condition changes. The condition is evaluated from an indicator result or a
    pandas ``eval`` expression. Use the ``|`` operator to attach to an
    indicator.

    Args:
        expr (str, optional): A pandas ``eval`` expression applied to the
            indicator result to produce a boolean/numeric signal. Omit if the
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
        expr: str | None = None,
        *,
        color: list[str] | str | None = None,
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

        if isinstance(color, list):
            color = np.where(flag > 0, color[1], color[0])

        ax.scatter(xv, yv, c=color, s=12 * 12, alpha=alpha, marker=marker)
