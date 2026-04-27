"""Markers primitive"""

import numpy as np

from ..model import BindingPrimitive
from ..utils import col_to_numpy


class Markers(BindingPrimitive):
    """Markers primitive.

    Plots scatter markers on the main pane at the close price whenever a
    condition changes. Bind a condition indicator via ``@`` or as the first
    positional argument. Compose the condition externally before binding.

    Args:
        indicator: indicator or expression returning a boolean/numeric signal.
            Markers appear at transition points (off→on, on→off).
            Can also be bound via ``@``.
        label (str, optional): Legend label. Omit to skip the legend entry.
        color (str or list of str, optional): Marker color. Pass a two-element
            list ``[color_off, color_on]`` to use different colors for signal
            transitions. Defaults to the matplotlib default color cycle.
        marker (str): Matplotlib marker symbol. Defaults to ``"."``.
        alpha (float): Opacity of the markers, between 0.0 and 1.0.
            Defaults to 0.6.

    Examples:
        (RSI(14) | (lambda s: s < 30)) @ Markers(color=["gray", "green"])
        Markers(RSI(14) | (lambda s: s < 30), color=["gray", "green"])
    """

    def __init__(
        self,
        indicator=None,
        *,
        label: str | None = None,
        color=None,
        marker: str = ".",
        alpha: float = 0.6,
    ):
        super().__init__(indicator)
        self.label = label
        self.color = color
        self.marker = marker
        self.alpha = alpha

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.main_axes()

        signal = chart.calc_result(prices, self.indicator)

        flag = np.clip(np.sign(np.asarray(signal, dtype=float)), 0, 1)
        close = np.asarray(col_to_numpy(prices, "close"), dtype=float)

        xs, flag, close = chart.mapper.series_xy(flag, close)

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

        xv = xs[mask]
        yv = close[mask]
        flag_at = flag[mask]

        marker = self.marker
        color = self.color
        alpha = self.alpha

        if isinstance(color, list):
            color = np.where(flag_at > 0, color[1], color[0])

        ax.scatter(xv, yv, c=color, s=12 * 12, alpha=alpha, marker=marker, label=self.label)
