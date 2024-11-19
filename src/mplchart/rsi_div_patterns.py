from dataclasses import dataclass
from mplchart.chart_pattern import ChartPatternProperties, ChartPattern, get_pivots_from_zigzag
from mplchart.line import Line, Pivot, Point
from mplchart.zigzag import Zigzag
from typing import List
import pandas as pd
import numpy as np
import logging

log = logging.getLogger(__name__)

@dataclass
class RsiDivergenceProperties(ChartPatternProperties):
    min_periods_lapsed: int = 5 # minimum number of days to form a pattern
    flat_ratio: float = 0.005 # maximum allowed

class RsiDivergencePattern(ChartPattern):
    def __init__(self, pivots: List[Pivot], divergence_line: Line):
        self.pivots = pivots
        self.pivots_count = len(pivots)
        self.divergence_line = divergence_line

    def get_pattern_name_by_id(self, id: int) -> str:
        pattern_names = {
            1: "Bullish",
            2: "Bearish",
            3: "Hidden Bullish",
            4: "Hidden Bearish",
        }
        return pattern_names[id]

    def resolve(self, properties: RsiDivergenceProperties) -> 'RsiDivergencePattern':
        if len(self.pivots) != 2:
            raise ValueError("Rsi Divergence must have 2 pivots")
        self.pattern_type = 0

        # makes prices always greater than the rsi values
        t1p1 = self.pivots[0].point.norm_price + 1
        t1p2 = self.pivots[1].point.norm_price + 1

        t2p1 = self.divergence_line.p1.norm_price
        t2p2 = self.divergence_line.p2.norm_price
        upper_angle = ((t1p2 - min(t2p1, t2p2)) / (t1p1 - min(t2p1, t2p2))
                      if t1p1 > t2p1 else
                      (t2p2 - min(t1p1, t1p2)) / (t2p1 - min(t1p1, t1p2)))
        lower_angle = ((t2p2 - max(t1p1, t1p2)) / (t2p1 - max(t1p1, t1p2))
                      if t1p1 > t2p1 else
                      (t1p2 - max(t2p1, t2p2)) / (t1p1 - max(t2p1, t2p2)))
        upper_line_dir = (1 if upper_angle > 1 + properties.flat_ratio else
                         -1 if upper_angle < 1 - properties.flat_ratio else 0)
        lower_line_dir = (-1 if lower_angle > 1 + properties.flat_ratio else
                          1 if lower_angle < 1 - properties.flat_ratio else 0)
        log.debug(f"pivots: {self.pivots[0].point.index}, {self.pivots[1].point.index}, "
                  f"rsi: {self.divergence_line.p1.norm_price}, {self.divergence_line.p2.norm_price}, "
                  f"upper_line_dir: {upper_line_dir}, lower_line_dir: {lower_line_dir}, "
                  f"upper_angle: {upper_angle}, lower_angle: {lower_angle}")

        if upper_line_dir == 1 and lower_line_dir == -1:
            if self.pivots[0].direction > 0:
                # higher high but lower RSI
                self.pattern_type = 2 # bearish
            elif self.pivots[0].direction < 0:
                # higher low but lower RSI
                self.pattern_type = 3 # hidden bullish
        elif upper_line_dir == -1 and lower_line_dir == 1:
            if self.pivots[0].direction > 0:
                # lower high but higher RSI
                self.pattern_type = 4 # hidden bearish
            elif self.pivots[0].direction < 0:
                # lower low but higher RSI
                self.pattern_type = 1 # bullish
        return self

def calc_rsi(prices: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate RSI"""
    series = prices["close"]
    ewm = dict(alpha=1.0 / period, min_periods=period, adjust=True, ignore_na=True)
    diff = series.diff()
    ups = diff.clip(lower=0).ewm(**ewm).mean()
    downs = diff.clip(upper=0).abs().ewm(**ewm).mean()

    return 100.0 - (100.0 / (1.0 + ups / downs))

def get_divergence_line(pivot1: Pivot, pivot2: Pivot, rsi: pd.Series) -> Line:
    """Get divergence line"""

    if pivot1.direction * pivot2.direction < 0:
        raise ValueError("Pivots must have the same direction")

    rsi1 = rsi.iloc[pivot1.point.index]
    rsi2 = rsi.iloc[pivot2.point.index]
    if np.isnan(rsi1) or np.isnan(rsi2):
        return None

    point1 = Point(pivot1.point.time, pivot1.point.index, rsi1, rsi1 / 100)
    point2 = Point(pivot2.point.time, pivot2.point.index, rsi2, rsi2 / 100)
    return Line(point1, point2)

def find_rsi_divergences(zigzag: Zigzag, offset: int, properties: RsiDivergenceProperties,
                         patterns: List[RsiDivergencePattern], rsi: pd.Series) -> bool:
    """
    Find RSI divergences using zigzag pivots

    Args:
        zigzag: Zigzag instance
        offset: Offset to start searching for pivots
        properties: RSI divergence properties
        patterns: List to store found patterns
        rsi: RSI series

    Returns:
        bool: True if a pattern is found, False otherwise
    """
    found = False
    pivots = []
    pivots_count = get_pivots_from_zigzag(zigzag, pivots, offset, 3)
    if pivots_count < 3:
        return False
    elif pivots[2].point.index - pivots[0].point.index + 1 < properties.min_periods_lapsed:
        return False
    else:
        divergence_line = get_divergence_line(pivots[0], pivots[2], rsi)
        if divergence_line is not None:
            pattern = RsiDivergencePattern([pivots[0], pivots[2]], divergence_line).resolve(properties)
            found = pattern.process_pattern(properties, patterns)
    return found
