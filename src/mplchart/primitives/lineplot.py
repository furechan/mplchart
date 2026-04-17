"""LinePlot primitive"""

import numpy as np

from ..model import Primitive
from ..utils import get_label, series_data


class LinePlot(Primitive):
    """
    Line Plot Primitive

    Plot any indicator as a line plot. Use the | operator to apply to an indicator.

    Args:
        item (str) :  name of the column to plot. default None
        style (str) : line style like 'solid', 'dashed', 'dotted', 'dashdot', 'marker'
        marker (str) : marker character like '.' or 'o'
        width (float) : line width override
        color (str) : color name or value
        alpha (float) : opacity value between 0.0 and 1.0
        target (str) : target pane as 'same', 'above', 'below'
        overbought (float) : level above which to shade a fill-between band
        oversold (float) : level below which to shade a fill-between band

    Examples:
        SMA(50) | LinePlot(style="dashdot", color="red")
        RSI(14) | LinePlot(overbought=70, oversold=30)
    """

    indicator = None

    def __init__(
        self,
        item: str | None = None,
        *,
        style: str | None = None,
        marker: str | None = None,
        width: float | None = None,
        color: str | None = None,
        alpha: float | None = None,
        target: str | None = None,
        overbought: float | None = None,
        oversold: float | None = None,
    ):
        if style == "marker":
            marker = marker or "."
            style = "none"

        self.item = item
        self.style = style
        self.marker = marker
        self.color = color
        self.width = width
        self.alpha = alpha
        self.target = target
        self.overbought = overbought
        self.oversold = oversold


    def __ror__(self, indicator):
        if not callable(indicator):
            return NotImplemented

        return self.clone(indicator=indicator)


    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.get_axes(self.target)

        result = chart.calc_result(prices, self.indicator)

        series = series_data(result, self.item)

        label = get_label(self.indicator)

        kwargs = dict(
            linestyle=self.style,
            linewidth=self.width,
            marker=self.marker,
            color=self.color,
            alpha=self.alpha,
        )

        xv, yv = chart.plot_xy(series)
        ax.plot(xv, yv, label=label, **kwargs)

        with np.errstate(invalid="ignore"):
            if self.oversold is not None:
                ax.fill_between(
                    xv, yv, self.oversold,
                    where=(yv <= self.oversold),
                    interpolate=True, alpha=0.5,
                )
            if self.overbought is not None:
                ax.fill_between(
                    xv, yv, self.overbought,
                    where=(yv >= self.overbought),
                    interpolate=True, alpha=0.5,
                )

