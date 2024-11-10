"""Triangle Pattern primitive"""

from typing import List
from dataclasses import replace

from ..model import Primitive
from ..trendlines import Zigzag, ScanProperties, TrendLine, find_pattern

def get_color(i) -> str:
    colors = ["red", "blue", "green", "purple", "orange", "brown"]
    return colors[i % len(colors)]

class ChartPattern(Primitive):
    """
    Chart Pattern Primitive
    Used to plot chart patterns

    Args:
        length (int) :  number of periods to lookback
        number_of_pivots (int) :  number of pivots in the pattern
        color (str) :  color of the chart pattern
    """

    def __init__(
            self, 
            item: str = None, 
            *,
            backcandels: int = 5, 
            forwardcandels: int = 5, 
            pivot_limit: int = 55, 
            scan_props: ScanProperties = None,
            color: str = "purple",
            axes: str = None
    ):
        self.item = item
        self.backcandels = backcandels
        self.forwardcandels = forwardcandels
        self.pivot_limit = pivot_limit
        self.color = color
        self.axes = axes

        self.scan_props = ScanProperties()
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
        ax.scatter(px, py, color=self.color, s=10 * 10, alpha=0.5, marker=".")
        for i, txt in enumerate(px):
            ax.annotate(txt, (px[i], py[i]))

        kwargs = dict(
            linestyle="-",
            linewidth=1.5,
            alpha=0.5,
        )

        # For each pattern, plot line segments between its points
        for pattern in patterns:
            # Use data.index to get the correct x positions
            line1_x = [pattern.trend_line1.p1.index, pattern.trend_line1.p2.index]
            line2_x = [pattern.trend_line2.p1.index, pattern.trend_line2.p2.index]
            line1_y = [pattern.trend_line1.p1.price, pattern.trend_line1.p2.price]
            line2_y = [pattern.trend_line2.p1.price, pattern.trend_line2.p2.price]
            xp = [pivot.point.index for pivot in pattern.pivots]
            yp = [pivot.point.price for pivot in pattern.pivots]

            color = get_color(xp[0])
            ax.scatter(xp, yp, color=color, s=11 * 11, alpha=0.5, marker="o")

            ax.plot(line1_x, line1_y, color=color, **kwargs)
            ax.plot(line2_x, line2_y, color=color, **kwargs)
            if line1_y[0] > line2_y[0]:
                ax.annotate(pattern.pattern_name, (line1_x[0], line1_y[0] * 1.01), color=color)
            else:
                ax.annotate(pattern.pattern_name, (line2_x[0], line2_y[0] * 1.01), color=color)

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
    patterns: List[TrendLine] = []
    
    # Find patterns
    for i in range(scan_props.offset, len(zigzag.zigzag_pivots)):
        find_pattern(zigzag, i, scan_props, patterns)
    
    return zigzag, patterns
