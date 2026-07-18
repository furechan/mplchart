"""AreaPlot primitive"""

from ..model.primitive import BindingPrimitive
from ..utils import get_label, series_data


class AreaPlot(BindingPrimitive):
    """
    Area Plot Primitive

    Plot any indicator or expression as an area plot. Use ``@`` to bind.

    Args:
        indicator: indicator or expression to plot. Can also be bound via ``@``.
        item (str) :  name of the column to plot. default None
        color (str) : color name or value
        alpha (float) : opacity value between 0.0 and 1.0
        label (str) : plot label

    Examples:
        AreaPlot(SMA(50), color="red", alpha=0.5)
        SMA(50) @ AreaPlot(color="red", alpha=0.5)
    """

    def __init__(
        self,
        indicator=None,
        *,
        item: str | None = None,
        color: str | None = None,
        alpha: float | None = None,
        label: str | None = None,
    ):
        if isinstance(indicator, str):
            item = item or indicator
            indicator = None

        super().__init__(indicator)
        self.item = item
        self.color = color
        self.alpha = alpha
        self.label = label

    def apply_to_chart(self, chart):
        ax = chart.get_axes()

        result = chart.calc_result(self.indicator)

        series = series_data(result, self.item)

        label = self.label or get_label(self.indicator)

        kwargs = dict(
            color=self.color,
            alpha=self.alpha,
        )

        xv, yv = chart.mapper.series_xy(series)
        ax.fill_between(
            xv,
            yv,
            0,
            label=label,
            interpolate=True,
            **kwargs,
        )
