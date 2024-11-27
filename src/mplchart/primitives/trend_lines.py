"""Triangle Pattern primitive"""

from typing import List
from dataclasses import replace

from auto_chart_patterns.zigzag import Zigzag
from auto_chart_patterns.trendline_patterns import TrendLineProperties, TrendLinePattern, find_trend_lines

from ..model import Primitive

def get_color(i) -> str:
    colors = ["red", "blue", "green", "purple", "orange", "brown"]
    return colors[i % len(colors)]

class TrendLine(Primitive):
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
            backcandles: int = 5,
            forwardcandles: int = 5,
            pivot_limit: int = 55,
            scan_props: TrendLineProperties = None,
            show_pivots: bool = False,
            axes: str = None
    ):
        self.item = item
        self.backcandles = backcandles
        self.forwardcandles = forwardcandles
        self.pivot_limit = pivot_limit
        self.show_pivots = show_pivots
        self.axes = axes

        self.scan_props = TrendLineProperties()
        if scan_props is not None:
            self.scan_props = replace(self.scan_props, **scan_props.__dict__)

    def process(self, data):
        if self.item:
            data = getattr(data, self.item)
        return extract_chart_patterns(
            data,
            backcandles=self.backcandles,
            forwardcandles=self.forwardcandles,
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
            linestyle="-",
            linewidth=1.5,
            alpha=0.5,
        )

        df = data.copy()
        # add row number as integer
        df['row_number'] = pd.RangeIndex(len(df))

        # For each pattern, plot line segments between its points
        for i, pattern in enumerate(patterns):
            # Use data.index to get the correct x positions
            line1_x = [df.loc[pattern.trend_line1.p1.time, 'row_number'],
                       df.loc[pattern.trend_line1.p2.time, 'row_number']]
            line2_x = [df.loc[pattern.trend_line2.p1.time, 'row_number'],
                       df.loc[pattern.trend_line2.p2.time, 'row_number']]
            line1_y = [pattern.trend_line1.p1.price, pattern.trend_line1.p2.price]
            line2_y = [pattern.trend_line2.p1.price, pattern.trend_line2.p2.price]
            xp = [df.loc[pivot.point.time, 'row_number'] for pivot in pattern.pivots]
            yp = [pivot.point.price for pivot in pattern.pivots]

            color = get_color(i)
            ax.scatter(xp, yp, color=color, s=10 * 10, alpha=0.5, marker="o")

            ax.plot(line1_x, line1_y, color=color, **kwargs)
            ax.plot(line2_x, line2_y, color=color, **kwargs)
            if line1_y[0] > line2_y[0]:
                if line1_y[0] > line1_y[1]:
                    ax.annotate(pattern.pattern_name, (line1_x[0], line1_y[0] * 1.02), color=color)
                else:
                    ax.annotate(pattern.pattern_name, (line1_x[1], line1_y[1] * 1.02), color=color)
            else:
                if line2_y[0] > line2_y[1]:
                    ax.annotate(pattern.pattern_name, (line2_x[0], line2_y[0] * 1.02), color=color)
                else:
                    ax.annotate(pattern.pattern_name, (line2_x[1], line2_y[1] * 1.02), color=color)

def extract_chart_patterns(prices, backcandles, forwardcandles, pivot_limit, scan_props):
    """
    extracts chart patterns.

    Args:
        prices (pd.DataFrame) : prices dataframe
        backcandles (int) : refers to minimum number bars required before
        forwardcandles (int) : refers to minimum number bars required after
        the local peak
        pivot_limit (int) : maximum distance between two pivots

    Return:
        A series of prices defined only at local peaks and equal to nan otherwize
    """

    zigzag = Zigzag(backcandles=backcandles, forwardcandles=forwardcandles, pivot_limit=pivot_limit, offset=0)
    zigzag.calculate(prices)

    # Initialize pattern storage
    patterns: List[TrendLinePattern] = []

    # Find patterns
    for i in range(scan_props.offset, len(zigzag.zigzag_pivots)):
        find_trend_lines(zigzag, i, scan_props, patterns)
    return zigzag, patterns
