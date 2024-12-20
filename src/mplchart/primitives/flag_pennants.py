"""Triangle Pattern primitive"""

from typing import List
from dataclasses import replace

from auto_chart_patterns.zigzag import Zigzag
from auto_chart_patterns.flag_pennant_patterns import FlagPennantProperties, \
    FlagPennantPattern, find_flags_and_pennants

from .trend_lines import TrendLine

class FlagPennant(TrendLine):
    """
    Flag Pennant Primitive
    Used to plot flag pennants

    Args:
        item (str) :  item to plot
        backcandles (int) :  number of periods to lookback
        forwardcandles (int) :  number of periods to lookforward
        pivot_limit (int) :  maximum distance between two pivots
        scan_props (TrendLineProperties) :  scan properties
        show_pivots (bool) :  whether to show pivots
        axes (str) :  axes to plot on
        patterns (List[TrendLinePattern]) :  patterns to plot
    """

    def __init__(
            self,
            item: str = None,
            *,
            backcandles: int = 5,
            forwardcandles: int = 5,
            pivot_limit: int = 55,
            scan_props: FlagPennantProperties = None,
            show_pivots: bool = False,
            axes: str = None,
            patterns: List[FlagPennantPattern] = None
    ):
        self.item = item
        self.backcandles = backcandles
        self.forwardcandles = forwardcandles
        self.pivot_limit = pivot_limit
        self.show_pivots = show_pivots
        self.axes = axes

        self.scan_props = FlagPennantProperties()
        if scan_props is not None:
            self.scan_props = replace(self.scan_props, **scan_props.__dict__)

        self.patterns = patterns

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
    patterns: List[FlagPennantPattern] = []

    # Find patterns
    for i in range(scan_props.offset, len(zigzag.zigzag_pivots)):
        find_flags_and_pennants(zigzag, i, scan_props, patterns)
    return zigzag, patterns
