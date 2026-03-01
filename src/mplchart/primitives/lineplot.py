"""LinePlot primitive"""


from ..model import Primitive
from ..utils import get_label, series_data, series_xy


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

    Examples:
        SMA(50) | LinePlot(style="dashdot", color="red")
    """

    indicator = None

    def __init__(
        self,
        item: str = None,
        *,
        style: str = None,
        marker: str = None,
        width: float = None,
        color: str = None,
        alpha: float = None,
        target: str = None
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


    def __ror__(self, indicator):
        if not callable(indicator):
            return NotImplemented

        return self.clone(indicator=indicator)


    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            target = self.target or chart.get_target(self.indicator)
            ax = chart.get_axes(target)

        result = chart.calc_result(prices, self.indicator)

        series = series_data(result, self.item, strict=True)
        series = chart.slice(series)

        label = get_label(self.indicator)

        kwargs = dict(
            linestyle=self.style,
            linewidth=self.width,
            marker=self.marker,
            color=self.color,
            alpha=self.alpha,
        )

        xv, yv = series_xy(series)
        ax.plot(xv, yv, label=label, **kwargs)

