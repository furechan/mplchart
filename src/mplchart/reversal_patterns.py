from dataclasses import dataclass
from typing import List, Optional
from .chart_pattern import ChartPattern, ChartPatternProperties, get_pivots_from_zigzag, \
    is_same_height
from .line import Pivot, Line, Point
from .zigzag import Zigzag
import pandas as pd
import logging

logger = logging.getLogger(__name__)

@dataclass
class ReversalPatternProperties(ChartPatternProperties):
    min_periods_lapsed: int = 15 # minimum number of days to form a pattern
    max_horizontal_ratio: float = 0.04 # maximum allowed ratio between aligned horizontal pivots

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
            same_height1, ratio1 = is_same_height(self.pivots[1], self.pivots[5],
                                                    self.pivots, properties.max_horizontal_ratio)
            if same_height1:
                same_height2, ratio2 = is_same_height(self.pivots[3], self.pivots[5],
                                                       self.pivots, properties.max_horizontal_ratio)
                ratio = ratio1 + ratio2
                if same_height2 and ratio <= properties.max_horizontal_ratio and ratio >= -properties.max_horizontal_ratio:
                    # 3 pivots are flat, we have a triple top or bottom
                    logger.debug(f"Pivots: {self.pivots[1].point.index}, {self.pivots[3].point.index}, "
                                 f"{self.pivots[5].point.index} are flat, ratio: {ratio:.4f}")
                    if self.pivots[0].direction < 0:
                        self.pattern_type = 3 # Triple Tops
                    else:
                        self.pattern_type = 4 # Triple Bottoms
                else:
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

def inspect_five_pivot_pattern(pivots: List[Pivot], properties: ReversalPatternProperties) -> bool:
    # check tops or bottoms are approximately flat
    same_height, _ = is_same_height(pivots[1], pivots[3], pivots, properties.max_horizontal_ratio)
    if same_height:
        if pivots[0].direction > 0:
            # may be a double bottom, check the sandle point price
            if pivots[2].point.price < pivots[0].point.price or \
                pivots[2].point.price < pivots[4].point.price:
                return True
        else:
            # may be a double top, check the sandle point price
            if pivots[2].point.price > pivots[0].point.price or \
                pivots[2].point.price > pivots[4].point.price:
                return True
    return False

def inspect_seven_pivot_pattern(pivots: List[Pivot], properties: ReversalPatternProperties) -> bool:
    # check the double sandle points price range and flat ratio
    if pivots[0].direction > 0:
        if pivots[2].point.price < pivots[0].point.price and \
            pivots[4].point.price < pivots[0].point.price:
            return True
    else:
        if pivots[2].point.price > pivots[0].point.price and \
            pivots[4].point.price > pivots[0].point.price:
            return True
    return False

def find_cross_point(line: Line, start_index: int, end_index: int, df: pd.DataFrame) -> Optional[Point]:
    if start_index > end_index:
        return None
    for i in range(start_index, end_index):
        current = df.iloc[i]
        high = current['high']
        low = current['low']
        price = line.get_price(i)
        if high >= price and low <= price:
            return Point(df.index[i], i, price)
    return None

def get_support_line(pivots: List[Pivot], start_index: int, end_index: int, df: pd.DataFrame) -> Optional[Line]:
    if len(pivots) > 2:
        raise ValueError("At most two points are required to form a line")
    if len(pivots) == 1:
        line = Line(pivots[0].point, pivots[0].point)
        cross_point2 = find_cross_point(line, pivots[0].point.index+1, end_index, df)
    else:
        line = Line(pivots[0].point, pivots[1].point)
        cross_point2 = find_cross_point(line, pivots[1].point.index+1, end_index, df)

    cross_point1 = find_cross_point(line, start_index, pivots[0].point.index, df)
    if cross_point1 is None:
        # the line is not crossing the chart on the left side
        return None
    # the cross point on the right side can be none as the chart is still trending
    if cross_point2 is None:
        cross_point2 = Point(df.index[end_index], end_index, line.get_price(end_index))
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

            index_delta = pivots[-1].point.index - pivots[0].point.index + 1
            if support_line is not None and index_delta >= properties.min_periods_lapsed:
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

                index_delta = pivots[-1].point.index - pivots[0].point.index + 1
                if support_line is not None and index_delta >= properties.min_periods_lapsed:
                    pattern = ReversalPattern(pivots, support_line).resolve(properties)
                    found = pattern.process_pattern(properties, patterns)

                    if found:
                        found_5_pattern = True

    return found_7_pattern or found_5_pattern


