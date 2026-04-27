"""BarPlot primitive"""

from ..model import BindingPrimitive
from ..utils import get_label, series_data


class BarPlot(BindingPrimitive):
    """
    Bar Plot Primitive

    Plot any indicator or expression as a bar plot. Use ``@`` to bind.

    Args:
        indicator: indicator or expression to plot. Can also be bound via ``@``.
        item (str) :  name of the column to plot. default None
        color (str) : color name or value
        alpha (float) : opacity value between 0.0 and 1.0
        width (float) : bar width setting
        target (str) : target pane as 'same', 'above', 'below'
        label (str) : plot label

    Examples:
        SMA(50) @ BarPlot(color="red", alpha=0.5)
        BarPlot(SMA(50), color="red", alpha=0.5)
    """

    def __init__(
        self,
        indicator=None,
        *,
        item: str | None = None,
        color: str | None = None,
        alpha: float | None = None,
        width: float | None = None,
        target: str | None = None,
        label: str | None = None,
    ):
        if isinstance(indicator, str):
            item = item or indicator
            indicator = None

        if width is None:
            width = 1.0

        super().__init__(indicator)
        self.item = item
        self.color = color
        self.alpha = alpha
        self.width = width
        self.target = target
        self.label = label

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.get_axes(self.target)

        result = chart.calc_result(prices, self.indicator)

        series = series_data(result, self.item)

        label = self.label or get_label(self.indicator)

        kwargs = dict(
            width=self.width,
            color=self.color,
            alpha=self.alpha,
        )

        xv, yv = chart.mapper.series_xy(series)
        ax.bar(xv, yv, label=label, **kwargs)
