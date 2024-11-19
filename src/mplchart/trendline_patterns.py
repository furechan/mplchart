from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
import pandas as pd
from .line import Point, Pivot, Line
from .zigzag import Zigzag
from .chart_pattern import ChartPattern, ChartPatternProperties, get_pivots_from_zigzag

import logging
logger = logging.getLogger(__name__)

@dataclass
class TrendLineProperties(ChartPatternProperties):
    number_of_pivots: int = 5 # minimum number of pivots to form a pattern
    error_ratio: float = 1e-6 # maximum allowed cosine difference between trend lines
    flat_ratio: float = 0.1 # maximum allowed flat ratio between trend lines
    flag_ratio: float = 1.5 # minimum allowed flag ratio between flag pole and flag width
    avoid_overlap: bool = True # whether to avoid overlapping patterns

class TrendLinePattern(ChartPattern):
    def __init__(self, pivots: List[Pivot], trend_line1: Line, trend_line2: Line):
        self.pivots = pivots
        self.trend_line1 = trend_line1
        self.trend_line2 = trend_line2

    def get_pattern_name_by_id(self, id: int) -> str:
        pattern_names = {
            1: "Ascending Channel",
            2: "Descending Channel",
            3: "Ranging Channel",
            4: "Rising Wedge (Expanding)",
            5: "Falling Wedge (Expanding)",
            6: "Diverging Triangle",
            7: "Ascending Triangle (Expanding)",
            8: "Descending Triangle (Expanding)",
            9: "Rising Wedge (Contracting)",
            10: "Falling Wedge (Contracting)",
            11: "Converging Triangle",
            12: "Descending Triangle (Contracting)",
            13: "Ascending Triangle (Contracting)",
            14: "Bull Pennant",
            15: "Bear Pennant",
            16: "Bull Flag",
            17: "Bear Flag"
        }
        return pattern_names.get(id, "Error")

    def resolve(self, properties: TrendLineProperties) -> 'TrendLinePattern':
        """
        Resolve pattern by updating trend lines, pivot points, and ratios

        Args:
            properties: ScanProperties object containing pattern parameters

        Returns:
            self: Returns the pattern object for method chaining
        """
        # Get first and last indices/times from pivots
        first_index = self.pivots[0].point.index
        last_index = self.pivots[-1].point.index
        first_time = self.pivots[0].point.time
        last_time = self.pivots[-1].point.time

        # Update trend line 1 endpoints
        self.trend_line1.p1 = Point(
            time=first_time,
            index=first_index,
            price=self.trend_line1.get_price(first_index),
            norm_price=self.trend_line1.get_norm_price(first_index)
        )
        self.trend_line1.p2 = Point(
            time=last_time,
            index=last_index,
            price=self.trend_line1.get_price(last_index),
            norm_price=self.trend_line1.get_norm_price(last_index)
        )

        # Update trend line 2 endpoints
        self.trend_line2.p1 = Point(
            time=first_time,
            index=first_index,
            price=self.trend_line2.get_price(first_index),
            norm_price=self.trend_line2.get_norm_price(first_index)
        )
        self.trend_line2.p2 = Point(
            time=last_time,
            index=last_index,
            price=self.trend_line2.get_price(last_index),
            norm_price=self.trend_line2.get_norm_price(last_index)
        )

        # Update pivot points to match trend lines
        for i, pivot in enumerate(self.pivots):
            # Determine which trend line to use based on pivot index
            if properties.number_of_pivots == 6:
                current_trend_line = self.trend_line1 if i % 2 == 1 else self.trend_line2
            else:
                current_trend_line = self.trend_line2 if i % 2 == 1 else self.trend_line1

            # Update pivot price to match trend line
            pivot.point.price = current_trend_line.get_price(pivot.point.index)
            pivot.point.norm_price = current_trend_line.get_norm_price(pivot.point.index)

        # Resolve pattern name/type
        self.resolve_pattern_name(properties)
        return self

    def resolve_pattern_name(self, properties: TrendLineProperties) -> 'TrendLinePattern':
        """Determine the pattern type based on trend lines and angles"""
        t1p1 = self.trend_line1.p1.norm_price
        t1p2 = self.trend_line1.p2.norm_price
        t2p1 = self.trend_line2.p1.norm_price
        t2p2 = self.trend_line2.p2.norm_price

        # Calculate angles between trend lines
        upper_angle = ((t1p2 - min(t2p1, t2p2)) / (t1p1 - min(t2p1, t2p2))
                      if t1p1 > t2p1 else
                      (t2p2 - min(t1p1, t1p2)) / (t2p1 - min(t1p1, t1p2)))

        lower_angle = ((t2p2 - max(t1p1, t1p2)) / (t2p1 - max(t1p1, t1p2))
                      if t1p1 > t2p1 else
                      (t1p2 - max(t2p1, t2p2)) / (t1p1 - max(t2p1, t2p2)))

        # Determine line directions
        upper_line_dir = (1 if upper_angle > 1 + properties.flat_ratio else
                         -1 if upper_angle < 1 - properties.flat_ratio else 0)

        lower_line_dir = (-1 if lower_angle > 1 + properties.flat_ratio else
                         1 if lower_angle < 1 - properties.flat_ratio else 0)

        # Calculate differences and ratios
        start_diff = abs(t1p1 - t2p1)
        end_diff = abs(t1p2 - t2p2)
        min_diff = min(start_diff, end_diff)
        bar_diff = self.trend_line1.p2.index - self.trend_line2.p1.index
        price_diff = abs(start_diff - end_diff) / bar_diff if bar_diff != 0 else 0

        probable_converging_bars = min_diff / price_diff if price_diff != 0 else float('inf')

        is_expanding = end_diff > start_diff
        is_contracting = start_diff > end_diff

        is_channel = (probable_converging_bars > 2 * bar_diff or
                     (not is_expanding and not is_contracting) or
                     (upper_line_dir == 0 and lower_line_dir == 0))

        invalid = np.sign(t1p1 - t2p1) != np.sign(t1p2 - t2p2)

        # Determine pattern type
        if invalid:
            self.pattern_type = 0
        elif is_channel:
            if upper_line_dir > 0 and lower_line_dir > 0:
                self.pattern_type = 1  # Ascending Channel
            elif upper_line_dir < 0 and lower_line_dir < 0:
                self.pattern_type = 2  # Descending Channel
            else:
                self.pattern_type = 3  # Ranging Channel
        elif is_expanding:
            if upper_line_dir > 0 and lower_line_dir > 0:
                self.pattern_type = 4  # Rising Wedge (Expanding)
            elif upper_line_dir < 0 and lower_line_dir < 0:
                self.pattern_type = 5  # Falling Wedge (Expanding)
            elif upper_line_dir > 0 and lower_line_dir < 0:
                self.pattern_type = 6  # Diverging Triangle
            elif upper_line_dir > 0 and lower_line_dir == 0:
                self.pattern_type = 7  # Ascending Triangle (Expanding)
            elif upper_line_dir == 0 and lower_line_dir < 0:
                self.pattern_type = 8  # Descending Triangle (Expanding)
        elif is_contracting:
            if upper_line_dir > 0 and lower_line_dir > 0:
                self.pattern_type = 9  # Rising Wedge (Contracting)
            elif upper_line_dir < 0 and lower_line_dir < 0:
                self.pattern_type = 10  # Falling Wedge (Contracting)
            elif upper_line_dir < 0 and lower_line_dir > 0:
                self.pattern_type = 11  # Converging Triangle
            elif lower_line_dir == 0:
                self.pattern_type = 12 if upper_line_dir < 0 else 1  # Descending Triangle (Contracting)
            elif upper_line_dir == 0:
                self.pattern_type = 13 if lower_line_dir > 0 else 2  # Ascending Triangle (Contracting)

        if properties.number_of_pivots == 4:
            # check flag ratio and difference
            flag_pole = abs(self.pivots[0].diff)
            flag_size = max(abs(self.trend_line1.p1.norm_price - self.trend_line2.p1.norm_price),
                            abs(self.trend_line1.p2.norm_price - self.trend_line2.p2.norm_price))
            if flag_size * properties.flag_ratio < flag_pole: # flag size must be smaller than its pole
                if self.pattern_type == 1 or self.pattern_type == 2 or self.pattern_type == 3:
                    # channel patterns
                    if self.pivots[0].direction > 0 and not self.pattern_type == 1:
                        self.pattern_type = 16  # Bull Flag
                    elif self.pivots[0].direction < 0 and not self.pattern_type == 2:
                        self.pattern_type = 17  # Bear Flag
                    else:
                        self.pattern_type = 0
                elif self.pattern_type == 9 or self.pattern_type == 10 or \
                    self.pattern_type == 11 or self.pattern_type == 12 or \
                    self.pattern_type == 13:
                    # pennant patterns
                    if self.pivots[0].direction > 0:
                        self.pattern_type = 14  # Bull Pennant
                    else:
                        self.pattern_type = 15  # Bear Pennant
                else:
                    self.pattern_type = 0
            else:
                # invalidate other pattern types
                self.pattern_type = 0

        return self

def calculate_cosine_diff(p1: Point, p2: Point, p3: Point, p4: Point) -> float:
    """Calculate cosine difference between two line segments

    Args:
        p1, p2: Points defining first line segment
        p3, p4: Points defining second line segment

    Returns:
        float: Cosine difference (0 to 2, where 0 means parallel)
    """
    # Calculate vectors from points
    v1 = np.array([p2.index - p1.index, p2.norm_price - p1.norm_price])
    v2 = np.array([p4.index - p3.index, p4.norm_price - p3.norm_price])

    # Calculate cosine similarity directly using dot product
    cos_sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

    return 1 - cos_sim

def is_aligned(first: Point, second: Point, third: Point, properties: TrendLineProperties) -> bool:
    # Calculate cosine difference directly from points
    cos_diff = calculate_cosine_diff(
        first, second,   # First line segment
        second, third    # Second line segment
    )
    basic_condition = 0 <= cos_diff and cos_diff <= properties.error_ratio

    if basic_condition:
        logger.debug(f"Points: {first.index}, {second.index}, {third.index} "
                     f"on the same line, cos_diff={cos_diff}")

    return basic_condition

def inspect_line_by_point(line: Line, point_bar: int, direction: float,
                         df: pd.DataFrame) -> Tuple[bool, float]:
    """
    Inspect a single line against price data from a pandas DataFrame

    Args:
        line: Line object to inspect
        point_bar: Index of the point to inspect
        direction: Direction of the trend (1 for up, -1 for down)
        df: DataFrame with 'open', 'high', 'low', 'close' columns

    Returns:
        Tuple of (valid: bool, diff: float)
    """
    # Get price data from DataFrame
    bar_data = df.iloc[point_bar]

    # Determine prices based on direction
    line_price = line.get_norm_price(point_bar)
    if direction > 0:
        # upper line
        body_high_price = max(bar_data['norm_open'], bar_data['norm_close'])
        if line_price < body_high_price:
            # invalid if line is crossing the candle body
            return False, float('inf') # make the difference as large as possible
        elif line_price > bar_data['norm_high']:
            # line is above the candle wick
            return True, line_price - bar_data['norm_high']
        else:
            # line is crossing the candle wick
            return True, 0
    else:
        # lower line
        body_low_price = min(bar_data['norm_open'], bar_data['norm_close'])
        if line_price > body_low_price:
            # invalid if line is crossing the candle body
            return False, float('inf') # make the difference as large as possible
        elif line_price < bar_data['norm_low']:
            # line is below the candle wick
            return True, bar_data['norm_low'] - line_price
        else:
            # line is crossing the candle wick
            return True, 0

def inspect_points(points: List[Point], direction: float, properties: TrendLineProperties,
                   df: pd.DataFrame) -> Tuple[bool, Line]:
    """
    Inspect multiple points to find the best trend line using DataFrame price data

    Args:
        points: List of points to create trend lines
        direction: Direction of the trend
        properties: Scan properties
        df: DataFrame with OHLC data

    Returns:
        Tuple of (valid: bool, best_trend_line: Line)
    """
    if len(points) == 3:
        aligned = is_aligned(points[0], points[1], points[2], properties)
        if not aligned:
            return False, None

        # Create three possible trend lines
        trend_line1 = Line(points[0], points[2])  # First to last
        # inspect line by middle point
        valid1, diff1 = inspect_line_by_point(trend_line1, points[1].index, direction, df)
        if valid1 and diff1 == 0:
            # prefer the line connecting the first and last points
            return True, trend_line1

        trend_line2 = Line(points[0], points[1])  # First to middle
        valid2, diff2 = inspect_line_by_point(trend_line2, points[2].index, direction, df)

        trend_line3 = Line(points[1], points[2])  # Middle to last
        valid3, diff3 = inspect_line_by_point(trend_line3, points[0].index, direction, df)

        if not valid1 and not valid2 and not valid3:
            return False, None

        # Find the best line
        if valid1:
            trendline = trend_line1
        elif valid2 and diff2 < diff1:
            trendline = trend_line2
        elif valid3 and diff3 < min(diff1, diff2):
            trendline = trend_line3

        return True, trendline
    else:
        # For 2 points, simply create one trend line
        trend_line = Line(points[0], points[1])
        return True, trend_line

def find_trend_lines(zigzag: Zigzag, offset: int, properties: TrendLineProperties,
                patterns: List[TrendLinePattern], df: pd.DataFrame) -> bool:
    """
    Find patterns using DataFrame price data

    Args:
        zigzag: ZigZag calculator instance
        offset: Offset to start searching for pivots
        properties: Scan properties
        patterns: List to store found patterns
        df: DataFrame with columns ['open', 'high', 'low', 'close']

    Returns:
        int: Index of the pivot that was used to find the pattern
    """
    # Get pivots
    if properties.number_of_pivots < 4 or properties.number_of_pivots > 6:
        raise ValueError("Number of pivots must be between 4 and 6")

    pivots = []
    min_pivots = get_pivots_from_zigzag(zigzag, pivots, offset, properties.number_of_pivots)
    if min_pivots != properties.number_of_pivots:
        return False

    # Validate pattern
    # Create point arrays for trend lines
    trend_points1 = ([pivots[0].point, pivots[2].point]
                        if properties.number_of_pivots == 4
                        else [pivots[0].point, pivots[2].point, pivots[4].point])
    trend_points2 = ([pivots[1].point, pivots[3].point, pivots[5].point]
                        if properties.number_of_pivots == 6
                        else [pivots[1].point, pivots[3].point])

    # Validate trend lines using DataFrame
    valid1, trend_line1 = inspect_points(trend_points1,
                                        np.sign(pivots[-1].direction),
                                        properties, df)
    valid2, trend_line2 = inspect_points(trend_points2,
                                        np.sign(pivots[-2].direction),
                                        properties, df)

    if valid1 and valid2:
        index_delta = pivots[-1].point.index - pivots[0].point.index + 1
        if index_delta < properties.min_periods_lapsed and \
            properties.number_of_pivots >= 5:
            # only consider patterns with enough time lapsed
            return False

        # Create pattern
        pattern = TrendLinePattern(
            pivots=pivots,
            trend_line1=trend_line1,
            trend_line2=trend_line2,
        ).resolve(properties)

        # Process pattern (resolve type, check if allowed, etc.)
        return pattern.process_pattern(properties, patterns)
