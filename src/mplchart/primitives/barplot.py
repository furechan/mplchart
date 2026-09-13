"""Bars primitive"""

import warnings
from ..canvas import PaneTarget
from ..model.primitive import BindingPrimitive
from ..utils import get_label, plot_vbars


class Bars(BindingPrimitive):
    """
    Bar Plot Primitive

    Plot any indicator or expression as a bar plot. Use ``@`` to bind.

    Args:
        indicator: indicator, expression, or already-computed series data
            (full-length prices-aligned; pandas date-indexed data aligns by
            date). ``@`` binds indicators/expressions only — pass data via
            the constructor.
        color (str): color name or value
        alpha (float): opacity value between 0.0 and 1.0
        legend (bool): include in the legend. Defaults to True — the label
            still names the plot for styling either way.
        width (float): bar width setting
        label (str): plot label

    Examples:
        Bars(SMA(50), color="red", alpha=0.5)
        SMA(50) @ Bars(color="red", alpha=0.5)
    """

    def __init__(
        self,
        indicator=None,
        *,
        color: str | None = None,
        alpha: float | None = None,
        width: float | None = None,
        label: str | None = None,
        legend: bool = True,
        pane: PaneTarget | None = None,
    ):

        if width is None:
            width = 1.0

        super().__init__(indicator)
        self.color = color
        self.alpha = alpha
        self.width = width
        self.label = label
        self.legend = legend
        self.pane = pane

    def apply_to_chart(self, chart):
        ax = chart.canvas.get_axes(self.pane)

        result = chart.view.eval(self.required_indicator())

        if hasattr(result, "columns"):
            raise ValueError(
                "Bars expects a single series; compose a single-output "
                "expression to select one column of a multi-output result."
            )
        series = result

        label = self.label if self.label is not None else get_label(self.indicator)
        color = chart.canvas.resolve_color(label, ax=ax, override=self.color, fallback="fill")
        label = label if self.legend else None

        xv, yv = chart.view.series_xy(series)
        plot_vbars(
            ax, xv, yv,
            width=self.width, color=color, alpha=self.alpha, label=label,
        )


class BarPlot(Bars):
    """Deprecated: use :class:`Bars` instead."""

    def __new__(cls, *args, **kwargs):
        warnings.warn(
            "BarPlot is deprecated; use Bars instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return super().__new__(cls)
