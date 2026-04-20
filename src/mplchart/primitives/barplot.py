"""BarPlot primitive"""


from ..model import Primitive
from ..utils import get_label, series_data


class BarPlot(Primitive):
    """
    Bar Plot Primitive

    Plot any indicator or expression as a bar plot. Use `|` with an indicator (pandas) or `@` with a pl.Expr (polars).

    Args:
        item (str) :  name of the column to plot. default None
        color (str) : color name or value
        alpha (float) : opacity value between 0.0 and 1.0
        width (float) : bar width setting
        target (str) : target pane as 'same', 'above', 'below'
        label (str) : plot label

    Examples:
        SMA(50) | BarPlot(color="red", alpha=0.5)   # indicator (pandas)
        SMA(50) @ BarPlot(color="red", alpha=0.5)   # expression (polars)
    """

    indicator = None

    def __init__(
        self,
        item: str | None = None,
        *,
        color: str | None = None,
        alpha: float | None = None,
        width: float | None = None,
        target: str | None = None,
        label: str | None = None

    ):
        if width is  None:
            width = 1.0

        self.item = item
        self.color = color
        self.alpha = alpha
        self.width = width
        self.target = target
        self.label = label

    def __ror__(self, indicator):
        if not callable(indicator):
            return NotImplemented

        return self.clone(indicator=indicator)

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

