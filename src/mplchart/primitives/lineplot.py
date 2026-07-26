"""LinePlot primitive"""

import numpy as np

from ..model.primitive import BindingPrimitive
from ..utils import get_label


class LinePlot(BindingPrimitive):
    """
    Line Plot Primitive

    Plot any indicator or expression as a line plot. Use ``@`` to bind.

    Args:
        indicator: indicator, expression, or already-computed series data
            (full-length prices-aligned; pandas date-indexed data aligns by
            date). ``@`` binds indicators/expressions only — pass data via
            the constructor.
        label (str) : legend label override. When None, derived from the indicator
            (the series name for data) — also the styling key for color settings.
        style (str) : line style like 'solid', 'dashed', 'dotted', 'dashdot', 'marker'
        marker (str) : marker character like '.' or 'o'
        width (float) : line width override
        color (str) : color name or value
        alpha (float) : opacity value between 0.0 and 1.0
        legend (bool) : include in the legend. Defaults to True — the label
            still names the plot for styling either way.
        pane (str) : pane to draw on — "main" or "twinx". Default the
            current pane. Selection only, never sticky — pane creation goes
            through the ``Pane`` primitive.
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
        legend: bool = True,
        pane: str | None = None,
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
        self.legend = legend
        self.pane = pane
        self.style = style
        self.marker = marker
        self.color = color
        self.width = width
        self.alpha = alpha
        self.overbought = overbought
        self.oversold = oversold

    def apply_to_chart(self, chart):
        ax = chart.canvas.get_axes(self.pane)

        result = chart.view.eval(self.required_indicator())

        if hasattr(result, "columns"):
            raise ValueError(
                "LinePlot expects a single series; compose a single-output "
                "expression to select one column of a multi-output result."
            )
        series = result

        label = self.label if self.label is not None else get_label(self.indicator)
        color = chart.canvas.resolve_color(label, ax, override=self.color, fallback="line")
        label = label if self.legend else None

        kwargs = dict(
            linestyle=self.style,
            linewidth=self.width,
            marker=self.marker,
            color=color,
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
