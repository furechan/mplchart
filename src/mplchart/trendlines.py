from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
from .line import Point, Pivot, Line
from .zigzag import Zigzag

@dataclass
class ScanProperties:
    offset: int = 0
    number_of_pivots: int = 5
    error_ratio: float = 0.02
    flat_ratio: float = 0.2
    flag_ratio: float = 0.8
    avoid_overlap: bool = True
    repaint: bool = False
    allowed_patterns: List[bool] = None
    allowed_last_pivot_directions: List[int] = None

def get_pattern_name_by_id(id: int) -> str:
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
        13: "Ascending Triangle (Contracting)"
    }
    return pattern_names.get(id, "Error")

class TrendLine:
    def __init__(self, pivots: List[Pivot], trend_line1: Line, trend_line2: Line):
        self.pivots = pivots
        self.trend_line1 = trend_line1
        self.trend_line2 = trend_line2
        self.pattern_type = 0
        self.pattern_name = ""

    def resolve(self, properties: ScanProperties) -> 'TrendLine':
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

    def resolve_pattern_name(self, properties: ScanProperties) -> 'TrendLine':
        """Determine the pattern type based on trend lines and angles"""
        t1p1 = self.trend_line1.p1.price
        t1p2 = self.trend_line1.p2.price
        t2p1 = self.trend_line2.p1.price
        t2p2 = self.trend_line2.p2.price

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
        
        is_expanding = abs(t1p2 - t2p2) > abs(t1p1 - t2p1)
        is_contracting = abs(t1p2 - t2p2) < abs(t1p1 - t2p1)
        
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

def is_same(first: Pivot, second: Pivot, third: Pivot, properties: ScanProperties) -> bool:
    # Calculate cosine difference directly from points
    cos_diff = calculate_cosine_diff(
        first.point, second.point,   # First line segment
        second.point, third.point    # Second line segment
    )
    basic_condition = 0 < cos_diff and cos_diff <= properties.error_ratio

    if basic_condition:
        print(f"pivots: {first.point.index}, {second.point.index}, {third.point.index} on the same line, cos_diff={cos_diff}")

    return basic_condition

def inspect_line(line: Line, starting_bar: int, ending_bar: int, other_bar: int, 
                direction: float, df: Optional[pd.DataFrame] = None) -> Tuple[bool, float]:
    """
    Inspect a single line against price data from a pandas DataFrame
    
    Args:
        line: Line object to inspect
        starting_bar: Start index for inspection
        ending_bar: End index for inspection
        other_bar: Index of the other point to check
        direction: Direction of the trend (1 for up, -1 for down)
        df: DataFrame with 'open', 'high', 'low', 'close' columns
    
    Returns:
        Tuple of (valid: bool, score: float)
    """
    valid = True
    score = 0.0
    
    for bar_index in range(starting_bar, ending_bar + 1):
        if df is None or bar_index >= len(df):
            continue
            
        # Get price data from DataFrame
        bar_data = df.iloc[bar_index]
        
        # Determine prices based on direction
        bar_price = bar_data['norm_high'] if direction > 0 else bar_data['norm_ low']
        bar_out_price = bar_data['norm_low'] if direction > 0 else bar_data['norm_high']
        line_price = line.get_price(bar_index)
        
        # Check if line is below the candle body for uptrend, or above for downtrend
        if line_price * direction < min(bar_data['norm_open'] * direction, bar_data['norm_close'] * direction):
            valid = False
            break
            
        # Score the line fit
        if (line_price * direction >= bar_out_price * direction and 
            line_price * direction <= bar_price * direction):
            score += 1
        # Check if line breaks at other bar
        elif bar_index == other_bar:
            valid = False
            break
            
    return valid, score

def inspect_points(points: List[Point], starting_bar: int, ending_bar: int, 
                  direction: float, df: Optional[pd.DataFrame] = None) -> Tuple[bool, Line]:
    """
    Inspect multiple points to find the best trend line using DataFrame price data
    
    Args:
        points: List of points to create trend lines
        starting_bar: Start index for inspection
        ending_bar: End index for inspection
        direction: Direction of the trend
        df: DataFrame with OHLC data
    
    Returns:
        Tuple of (valid: bool, best_trend_line: Line)
    """
    if len(points) == 3:
        # Create three possible trend lines
        trend_line1 = Line(points[0], points[2])  # First to last
        trend_line2 = Line(points[0], points[1])  # First to middle
        trend_line3 = Line(points[1], points[2])  # Middle to last
        
        # Inspect each line
        valid1, score1 = inspect_line(trend_line1, starting_bar, ending_bar, points[1].index, direction, df)
        valid2, score2 = inspect_line(trend_line2, starting_bar, ending_bar, points[2].index, direction, df)
        valid3, score3 = inspect_line(trend_line3, starting_bar, ending_bar, points[0].index, direction, df)
        
        # Find the best line
        if valid1 and score1 > max(score2, score3):
            return True, trend_line1
        elif valid2 and score2 > max(score1, score3):
            return True, trend_line2
        else:
            return valid3, trend_line3
    else:
        # For 2 points, simply create and inspect one trend line
        trend_line = Line(points[0], points[-1])
        valid, _ = inspect_line(trend_line, starting_bar, ending_bar, points[0].index, direction, df)
        return valid, trend_line

def find_pattern(zigzag: Zigzag, offset: int, properties: ScanProperties, 
                patterns: List[TrendLine], df: Optional[pd.DataFrame] = None, 
                max_live_patterns: int = 20):
    """
    Find patterns using DataFrame price data
    
    Args:
        zigzag: ZigZag calculator instance
        offset: Offset to start searching for pivots
        properties: Scan properties
        d_properties: Drawing properties
        patterns: List to store found patterns
        df: DataFrame with columns ['open', 'high', 'low', 'close']
        max_live_patterns: Maximum number of patterns to track
    
    Returns:
        int: Index of the pivot that was used to find the pattern
    """
    # Get pivots
    pivots = []
    for i in range(properties.number_of_pivots):
        pivot = zigzag.get_pivot(i + offset)
        if pivot is None:
            return
        # zigzag pivots are in reverse order
        pivots.insert(0, pivot.deep_copy())

    # Validate pattern
    valid_pattern = False
    if properties.number_of_pivots == 6:
        valid_pattern = (is_same(pivots[0], pivots[2], pivots[4], properties) and 
                        is_same(pivots[1], pivots[3], pivots[5], properties))
    else:
        valid_pattern = is_same(pivots[0], pivots[2], pivots[4], properties)

    if valid_pattern:
        # Create point arrays for trend lines
        trend_points1 = [pivots[0].point, pivots[2].point, pivots[4].point]
        trend_points2 = ([pivots[1].point, pivots[3].point, pivots[5].point] 
                        if properties.number_of_pivots == 6 
                        else [pivots[1].point, pivots[3].point])
        
        first_index = pivots[0].point.index
        last_index = pivots[-1].point.index
        
        # Validate trend lines using DataFrame
        valid1, trend_line1 = inspect_points(trend_points1, first_index, last_index, 
                                           np.sign(pivots[-1].direction), df)
        valid2, trend_line2 = inspect_points(trend_points2, first_index, last_index, 
                                           np.sign(pivots[-2].direction), df)

        if valid1 and valid2:

            # Create pattern
            pattern = TrendLine(
                pivots=pivots,
                trend_line1=trend_line1,
                trend_line2=trend_line2,
            ).resolve(properties)
            print(f"Pattern candidate: {pattern.pattern_name}, pivot_index={pivots[0].point.index}")
            
            # Process pattern (resolve type, check if allowed, etc.)
            if not process_pattern(pattern, properties, patterns, max_live_patterns):
                print(f"Failed to process pattern {pattern.pattern_name}")

def process_pattern(pattern: TrendLine, properties: ScanProperties, 
                   patterns: List[TrendLine], max_live_patterns: int) -> bool:
    """
    Process a new pattern: validate it, check if it's allowed, and manage pattern list
    
    Args:
        pattern: The pattern to process
        properties: Scan properties
        patterns: List of existing patterns
        max_live_patterns: Maximum number of patterns to keep
        draw: Whether to draw the pattern
        
    Returns:
        bool: True if pattern was successfully processed and added
    """
    # Log warning if invalid pattern type detected
    if pattern.pattern_type == 0:
        print(f'Warning: Wrong Type detected {pattern.pattern_type}, ' + 
              f'Upper/Lower Line Dirs, Invalid pattern detected')
        return False
    
    # Get last direction from the last pivot
    last_dir = np.sign(pattern.pivots[-1].direction)
    
    # Get allowed last pivot direction for this pattern type
    allowed_last_pivot_direction = 0
    if properties.allowed_last_pivot_directions is not None:
        if pattern.pattern_type < len(properties.allowed_last_pivot_directions):
            allowed_last_pivot_direction = properties.allowed_last_pivot_directions[pattern.pattern_type]
    
    # Check if pattern type is allowed
    pattern_allowed = True
    if properties.allowed_patterns is not None:
        if pattern.pattern_type >= len(properties.allowed_patterns):
            pattern_allowed = False
        else:
            pattern_allowed = (pattern.pattern_type >= 0 and 
                             properties.allowed_patterns[pattern.pattern_type])
    
    # Check if direction is allowed
    direction_allowed = (allowed_last_pivot_direction == 0 or 
                        allowed_last_pivot_direction == last_dir)
    
    if pattern_allowed and direction_allowed:
        # Check for existing pattern with same pivots
        existing_pattern = False
        existing_pattern_index = -1
        existing_ratio_diff = 5.0
        
        for idx, existing in enumerate(patterns):
            # Check if pivots match
            match = True
            for i in range(len(pattern.pivots)):
                if pattern.pivots[i].point.index != existing.pivots[i].point.index:
                    match = False
                    break
            
            if match:
                existing_pattern = True
                existing_pattern_index = idx
                existing_ratio_diff = existing.ratio_diff
                break
        
        # Determine if we should replace existing pattern
        delete_old = existing_pattern and existing_ratio_diff > pattern.ratio_diff
        
        if delete_old or not existing_pattern:
            # Set pattern name
            pattern.pattern_name = get_pattern_name_by_id(pattern.pattern_type)
            
            # Delete old pattern if necessary
            if delete_old:
                patterns.pop(existing_pattern_index)
            
            # Add new pattern and manage list size
            patterns.append(pattern)
            while len(patterns) > max_live_patterns:
                patterns.pop(0)
            
            return True
    
    return False