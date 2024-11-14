from dataclasses import dataclass
from typing import List, Optional
from .chart_pattern import ChartPattern, ChartPatternProperties, get_pivots_from_zigzag
from .line import Pivot, Line, Point
from .zigzag import Zigzag
import pandas as pd

@dataclass
class ReversalPatternProperties(ChartPatternProperties):
    min_periods_lapsed: int = 21 # minimum number of days to form a pattern
    peak_diff_threshold: float = 2e-3 # maximum allowed

class ReversalPattern(ChartPattern):
    def __init__(self, pivots: List[Pivot], support_line: Line):
        self.pivots = pivots
        self.pivots_count = len(pivots)
        self.support_line = support_line

    def get_pattern_name_by_id(self, id: int) -> str:
        pattern_names = {
            1: "Double Tops",
            2: "Double Bottoms",
            3: "Triple Tops",
            4: "Triple Bottoms",
            5: "Head and Shoulders",
            6: "Inverted Head and Shoulders",
        }
        return pattern_names[id]

    def resolve(self, properties: ReversalPatternProperties) -> 'ReversalPattern':
        self.pattern_type = 0
        if self.pivots_count == 5:
            if self.pivots[0].direction < 0:
                self.pattern_type = 1 # Double Tops
            else:
                self.pattern_type = 2 # Double Bottoms
        elif self.pivots_count == 7:
            # check the flat ratio of the 4th and 6th points
            if check_flat_ratio(self.pivots[3].cross_diff, properties) and \
                check_flat_ratio(self.pivots[5].cross_diff, properties):
                # 3 pivots are flat, we have a triple top or bottom
                if self.pivots[0].direction < 0:
                    self.pattern_type = 3 # Triple Tops
                else:
                    self.pattern_type = 4 # Triple Bottoms
            elif check_flat_ratio(
                    self.pivots[1].point.norm_price - self.pivots[5].point.norm_price,
                    properties):
                # two shoulders should be approximately flat
                if self.pivots[0].direction < 0 and self.pivots[3].cross_diff > 0 and \
                    self.pivots[5].cross_diff < 0:
                    # side peaks lower than the middle peak
                    self.pattern_type = 5 # Head and Shoulders
                elif self.pivots[0].direction > 0 and self.pivots[3].cross_diff < 0 and \
                    self.pivots[5].cross_diff > 0:
                    self.pattern_type = 6 # Inverted Head and Shoulders
        else:
            raise ValueError("Invalid number of pivots")
        return self

def check_flat_ratio(diff: float, properties: ReversalPatternProperties) -> bool:
    # high pivot or low pivot is approximately flat with the previous high or low
    return abs(diff) <= properties.peak_diff_threshold

def inspect_five_pivot_pattern(pivots: List[Pivot], properties: ReversalPatternProperties) -> bool:
    # check tops or bottoms are approximately flat
    if check_flat_ratio(pivots[3].cross_diff, properties):
        if pivots[0].direction > 0:
            # may be a double bottom, check the sandle point price
            if pivots[2].point.norm_price < pivots[0].point.norm_price or \
                pivots[2].point.norm_price < pivots[4].point.norm_price:
                return True
        else:
            # may be a double top, check the sandle point price
            if pivots[2].point.norm_price > pivots[0].point.norm_price or \
                pivots[2].point.norm_price > pivots[4].point.norm_price:
                return True
    return False

def inspect_seven_pivot_pattern(pivots: List[Pivot], properties: ReversalPatternProperties) -> bool:
    # check the double sandle points price range and flat ratio
    #if abs(pivots[4].cross_diff) > properties.sandle_flat_ratio:
    #    return False
    if pivots[0].direction > 0:
        # may be a triple bottome, check the double sandle points
        if (pivots[2].point.norm_price > pivots[0].point.norm_price and \
            pivots[2].point.norm_price > pivots[6].point.norm_price) or \
            (pivots[4].point.norm_price > pivots[0].point.norm_price and \
                pivots[4].point.norm_price > pivots[6].point.norm_price):
            return False
    else:
        # may be a triple top, check the double sandle points
        if (pivots[2].point.norm_price < pivots[0].point.norm_price and \
            pivots[2].point.norm_price < pivots[6].point.norm_price) or \
            (pivots[4].point.norm_price < pivots[0].point.norm_price and \
                pivots[4].point.norm_price < pivots[6].point.norm_price):
            return False
    return True

def find_cross_point(line: Line, start_index: int, end_index: int, df: pd.DataFrame) -> Optional[Point]:
    if start_index > end_index:
        return None
    for i in range(start_index, end_index):
        current = df.iloc[i]
        high = current['norm_high']
        low = current['norm_low']
        norm_price = line.get_norm_price(i)
        if high >= norm_price and low <= norm_price:
            return Point(df.index[i], i, line.get_price(i), norm_price)
    return None

def get_support_line(pivots: List[Pivot], start_index: int, end_index: int, df: pd.DataFrame) -> Optional[Line]:
    if len(pivots) > 2:
        raise ValueError("At most two points are required to form a line")
    if len(pivots) == 1:
        line = Line(pivots[0].point, pivots[0].point)
    else:
        line = Line(pivots[0].point, pivots[1].point)

    cross_point1 = find_cross_point(line, start_index, pivots[0].point.index, df)
    if cross_point1 is None:
        # the line is not crossing the chart on the left side
        return None
    # the cross point on the right side can be none as the chart is still trending
    cross_point2 = Point(df.index[end_index], end_index,
                         line.get_price(end_index),
                         line.get_norm_price(end_index))
    return Line(cross_point1, cross_point2)

def find_reversal_patterns(zigzag: Zigzag, offset: int, properties: ReversalPatternProperties,
                  patterns: List[ReversalPattern], df: pd.DataFrame) -> bool:
    """
    Find reversal patterns using zigzag pivots

    Args:
        zigzag: Zigzag instance
        offset: Offset to start searching for pivots
        properties: Reversal pattern properties
        patterns: List to store found patterns
        df: DataFrame with columns ['open', 'high', 'low', 'close']

    Returns:
        List[ReversalPattern]: Found patterns
    """
    found_7_pattern = False
    found_5_pattern = False
    pivots = []
    pivots_count = get_pivots_from_zigzag(zigzag, pivots, offset, 7)
    if pivots_count == 7:
        if inspect_seven_pivot_pattern(pivots, properties):
            # we may have a triple top or bottom or head and shoulders
            support_line = get_support_line(
                [pivots[2], pivots[4]], pivots[0].point.index, pivots[6].point.index, df)

            time_delta = pivots[-1].point.time - pivots[0].point.time
            if support_line is not None and time_delta.days + 1 >= properties.min_periods_lapsed:
                pattern = ReversalPattern(pivots, support_line).resolve(properties)
                found_7_pattern = pattern.process_pattern(properties, patterns)

    # continue to inspect 5 point pattern
    if pivots_count >= 5:
        for i in range(0, pivots_count - 5 + 1):
            pivots = []
            get_pivots_from_zigzag(zigzag, pivots, offset + i, 5) # check the last 5 pivots as the pivots are in reverse order
            if inspect_five_pivot_pattern(pivots, properties):
                # use the sandle point to form a support line
                support_line = get_support_line(
                    [pivots[2]], pivots[0].point.index, pivots[4].point.index, df)

                time_delta = pivots[-1].point.time - pivots[0].point.time
                if support_line is not None and time_delta.days + 1 >= properties.min_periods_lapsed:
                    pattern = ReversalPattern(pivots, support_line).resolve(properties)
                    found = pattern.process_pattern(properties, patterns)

                    if found:
                        found_5_pattern = True

    return found_7_pattern or found_5_pattern


