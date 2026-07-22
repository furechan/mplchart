"""LinePlot primitive"""

import numpy as np

from ..model.primitive import BindingPrimitive
from ..utils import get_label


class LinePlot(BindingPrimitive):
    """
    Line Plot Primitive

    Plot any indicator or expression as a line plot. Use ``@`` to bind.

    Args:
        indicator: indicator or expression to plot. Can also be bound via ``@``.
        label (str) : legend label override. When None, derived from the indicator.
        style (str) : line style like 'solid', 'dashed', 'dotted', 'dashdot', 'marker'
        marker (str) : marker character like '.' or 'o'
        width (float) : line width override
        color (str) : color name or value
        alpha (float) : opacity value between 0.0 and 1.0
        overbought (float) : level above which to shade a fill-between band
        oversold (float) : level below which to shade a fill-between band

    Examples:
        LinePlot(SMA(50), style="dashdot", color="red")
        LinePlot(RSI(14), overbought=70, oversold=30)
        SMA(50) @ LinePlot(style="dashdot", color="red")
    """

    def __init__(
        self,
        indicator=None,
        *,
        label: str | None = None,
        style: str | None = None,
        marker: str | None = None,
        width: float | None = None,
        color: str | None = None,
        alpha: float | None = None,
        overbought: float | None = None,
        oversold: float | None = None,
    ):

        if style == "marker":
            marker = marker or "."
            style = "none"

        super().__init__(indicator)
        self.label = label
        self.style = style
        self.marker = marker
        self.color = color
        self.width = width
        self.alpha = alpha
        self.overbought = overbought
        self.oversold = oversold

    def apply_to_chart(self, chart):
        ax = chart.canvas.get_axes()

        result = chart.view.eval(self.required_indicator())

        if hasattr(result, "columns"):
            raise ValueError(
                "LinePlot expects a single series; compose a single-output "
                "expression to select one column of a multi-output result."
            )
        series = result

        label = self.label or get_label(self.indicator)

        kwargs = dict(
            linestyle=self.style,
            linewidth=self.width,
            marker=self.marker,
            color=self.color,
            alpha=self.alpha,
        )

        xv, yv = chart.view.series_xy(series)
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
