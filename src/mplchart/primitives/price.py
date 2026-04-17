"""Price primitive"""

from matplotlib import pyplot as plt

from ..model import Primitive
from ..utils import calc_price


class Price(Primitive):
    """Price primitive.

    Plots a single price series as a line. Rendered on the same scale as the
    main price chart.

    Args:
        item (str): Name of the price series to plot. One of ``"open"``,
            ``"high"``, ``"low"``, ``"close"``, ``"avg"``, ``"mid"``,
            ``"typ"``, ``"wcl"``, or any column in the prices DataFrame.
            Defaults to ``"close"``.
        width (float): Line width. Defaults to 1.0.
        alpha (float): Opacity of the line, between 0.0 and 1.0. Defaults to 1.0.
        color (str, optional): Line color. Defaults to the current
            ``text.color`` matplotlib parameter.

    Examples:
        Price()           # plot the close price
        Price("open")     # plot the open price
    """

    def __init__(
        self,
        item: str = "close",
        *,
        width: float = 1.0,
        alpha: float = 1.0,
        color: str | None = None,
    ):
        self.item = item
        self.width = width
        self.alpha = alpha
        self.color = color


    def __call__(self, prices):
        return calc_price(prices, self.item)


    def plot_handler(self, prices, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        series = self(prices)
        xv, yv = chart.plot_xy(series)

        textcolor = plt.rcParams["text.color"]

        label = repr(self)
        width = self.width
        alpha = self.alpha
        color = self.color or textcolor

        ax.plot(xv, yv, label=label, linewidth=width, alpha=alpha, color=color)
