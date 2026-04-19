"""AreaPlot primitive"""


from ..model import Primitive
from ..utils import get_label, series_data


class AreaPlot(Primitive):
    """
    Area Plot Primitive

    Plot any indicator or expression as an area plot. Use `|` with an indicator (pandas) or `@` with a pl.Expr (polars).

    Args:
        item (str) :  name of the column to plot. default None
        color (str) : color name or value
        alpha (float) : opacity value between 0.0 and 1.0
        target (str) : target pane as like 'same', 'above', 'below'
        label (str) : plot label

    Examples:
        SMA(50) | AreaPlot(color="red", alpha=0.5)   # indicator (pandas)
        SMA(50) @ AreaPlot(color="red", alpha=0.5)   # expression (polars)
    """

    indicator = None

    def __init__(
        self,
        item: str | None = None,
        *,
        color: str | None = None,
        alpha: float | None = None,
        target: str | None = None,
        label: str | None = None,
    ):
        self.item = item
        self.color = color
        self.alpha = alpha
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
            color=self.color,
            alpha=self.alpha,
        )

        xv, yv = chart.plot_xy(series)
        ax.fill_between(
            xv,
            yv,
            0,
            label=label,
            interpolate=True,
            **kwargs,
        )
