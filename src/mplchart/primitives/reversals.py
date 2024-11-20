"""Triangle Pattern primitive"""

from typing import List
from dataclasses import replace

from ..model import Primitive
from ..reversal_patterns import Zigzag, ReversalPatternProperties, ReversalPattern, find_reversal_patterns

def get_color(i) -> str:
    colors = ["darkred", "darkblue", "darkgreen", "darkorange"]
    return colors[i % len(colors)]

class Reversal(Primitive):
    """
    Chart Pattern Primitive
    Used to plot chart patterns

    Args:
        item (str) :  item to plot
        backcandels (int) :  number of periods to lookback
        forwardcandels (int) :  number of periods to lookforward
        pivot_limit (int) :  maximum number of pivots to consider
        scan_props (ReversalPatternProperties) :  scan properties
        show_pivots (bool) :  whether to show pivots
        axes (str) :  axes to plot on
    """

    def __init__(
            self,
            item: str = None,
            *,
            backcandels: int = 5,
            forwardcandels: int = 5,
            pivot_limit: int = 55,
            scan_props: ReversalPatternProperties = None,
            show_pivots: bool = False,
            axes: str = None
    ):
        self.item = item
        self.backcandels = backcandels
        self.forwardcandels = forwardcandels
        self.pivot_limit = pivot_limit
        self.show_pivots = show_pivots
        self.axes = axes

        self.scan_props = ReversalPatternProperties()
        if scan_props is not None:
            self.scan_props = replace(self.scan_props, **scan_props.__dict__)

    def process(self, data):
        if self.item:
            data = getattr(data, self.item)
        return extract_chart_patterns(
            data,
            backcandels=self.backcandels,
            forwardcandels=self.forwardcandels,
            pivot_limit=self.pivot_limit,
            scan_props=self.scan_props
        )

    def plot_handler(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes()

        zigzag, patterns = self.process(data)

        px = [pivot.point.index for pivot in zigzag.zigzag_pivots]
        py = [pivot.point.price for pivot in zigzag.zigzag_pivots]
        if self.show_pivots:
            ax.scatter(px, py, color="purple", s=10 * 10, alpha=0.5, marker=".")
            for i, txt in enumerate(px):
                ax.annotate(txt, (px[i], py[i]))

        kwargs = dict(
            linestyle="--",
            linewidth=1.5,
            alpha=0.5,
        )

        # For each pattern, plot line segments between its points
        for i, pattern in enumerate(patterns):
            # Use data.index to get the correct x positions
            line1_x = [pattern.support_line.p1.index, pattern.support_line.p2.index]
            line1_y = [pattern.support_line.p1.price, pattern.support_line.p2.price]
            xp = [pivot.point.index for pivot in pattern.pivots]
            yp = [pivot.point.price for pivot in pattern.pivots]

            color = get_color(i)
            ax.scatter(xp, yp, color=color, s=10 * 10, alpha=0.5, marker="o")

            ax.plot(line1_x, line1_y, color=color, **kwargs)
            sandle_point = pattern.pivots[2]
            text_x = sandle_point.point.index
            text_y = sandle_point.point.price
            if sandle_point.direction > 0:
                text_x
                text_y *= 1.02
            else:
                text_x
                text_y *= 0.97
            ax.annotate(pattern.pattern_name, (text_x, text_y), color=color)


def extract_chart_patterns(prices, backcandels, forwardcandels, pivot_limit, scan_props):
    """
    extracts chart patterns.

    Args:
        length (int) : refers to minimum number bars required before
        and after the local peak
        number_of_pivots (int) : number of pivots in the pattern

    Return:
        A series of prices defined only at local peaks and equal to nan otherwize
    """

    zigzag = Zigzag(backcandels=backcandels, forwardcandels=forwardcandels, pivot_limit=pivot_limit, offset=0)
    zigzag.calculate(prices)

    # Initialize pattern storage
    patterns: List[ReversalPattern] = []

    # Find patterns
    for i in range(scan_props.offset, len(zigzag.zigzag_pivots)):
        find_reversal_patterns(zigzag, i, scan_props, patterns, prices)

    return zigzag, patterns
