"""AreaPlot primitive"""


from ..model import Primitive
from ..utils import get_label, series_data, series_xy


class AreaPlot(Primitive):
    """
    Area Plot Primitive

    Plot any indicator as an area plot. Use the | operator to apply to an indicator.

    Args:
        item (str) :  name of the column to plot. default None
        color (str) : color name or value
        alpha (float) : opacity value between 0.0 and 1.0
        axes (str) : target axes like 'same', 'above', 'below'
        label (str) : plot label

    Examples:
        SMA(50) | AreaPlot(color="red", alpha=0.5)
    """

    indicator = None

    def __init__(
        self,
        item: str = None,
        *,
        color: str = None,
        alpha: float = None,
        axes: str = None,
        label: str = None,
    ):
        self.item = item
        self.color = color
        self.alpha = alpha
        self.axes = axes
        self.label = label

    def __ror__(self, indicator):
        if not callable(indicator):
            return NotImplemented

        return self.clone(indicator=indicator)

    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            target = self.axes or chart.get_target(self.indicator)
            ax = chart.get_axes(target)

        result = chart.calc_result(prices, self.indicator)

        data = series_data(result, self.item, strict=True)

        data = chart.slice(data)

        label = self.label or get_label(self.indicator)

        kwargs = dict(
            color=self.color,
            alpha=self.alpha,
        )

        xv, yv = series_xy(data)
        ax.fill_between(
            xv,
            yv,
            0,
            label=label,
            interpolate=True,
            **kwargs,
        )
