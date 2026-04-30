"""Stripes primitive"""

import numpy as np

from ..model import BindingPrimitive


class Stripes(BindingPrimitive):
    """Stripes primitive.

    Shades vertical bands across all chart panes during periods when a
    condition is active. Bind a condition indicator via ``@`` or as the
    first positional argument.

    Args:
        indicator: indicator or expression returning a boolean/numeric signal.
            Positive values shade the band; zero or negative do not.
            Can also be bound via ``@``.
        label (str, optional): Legend label. Omit to skip the legend entry.
        color (str, optional): Fill color for the shaded regions.
        alpha (float, optional): Opacity of the shaded regions, between 0.0
            and 1.0.

    Examples:
        Stripes(RSI(14) | (lambda s: s < 30), color="green", alpha=0.15)
        (RSI(14) < 30) @ Stripes(color="green", alpha=0.15)
    """

    def __init__(self, indicator=None, *, label: str | None = None, color=None, alpha=None):
        super().__init__(indicator)
        self.label = label
        self.color = color
        self.alpha = alpha

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.root_axes()

        result = chart.calc_result(prices, self.indicator)

        xs, values = chart.mapper.series_xy(result)

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

        label = self.label
        for s, e in zip(starts, ends):
            ax.axvspan(xs[s], xs[e - 1], color=color, alpha=alpha, label=label)
            label = None  # only label the first span so legend shows one entry
