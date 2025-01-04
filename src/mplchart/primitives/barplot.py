"""BarPlot primitive"""


from ..model import Primitive
from ..utils import get_label, series_data, series_xy


class BarPlot(Primitive):
    """
    Bar Plot Primitive

    Plot any indicator as an bar plot. Use the | operator to apply to an indicator.

    Args:
        item (str) :  name of the column to plot. default None
        color (str) : color name or value
        alpha (float) : opacity value between 0.0 and 1.0
        width (float) : bar width setting
        axes (str) : target axes like 'same', 'above', 'below'
        label (str) : plot label

    Examples:
        SMA(50) | BarPlot(color="red", alpha=0.5)
    """

    indicator = None

    def __init__(
        self,
        item: str = None,
        *,
        color: str = None,
        alpha: float = None,
        width: float = None,
        axes: str = None,
        label: str = None

    ):
        if width is  None:
            width = 1.0

        self.item = item
        self.color = color
        self.alpha = alpha
        self.width = width
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
            width=self.width,
            color=self.color,
            alpha=self.alpha,
        )

        xv, yv = series_xy(data)
        ax.bar(xv, yv, label=label, **kwargs)

