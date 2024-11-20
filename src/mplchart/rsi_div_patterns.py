from dataclasses import dataclass
from mplchart.chart_pattern import ChartPatternProperties
from mplchart.line import Line, Point
from mplchart.zigzag import window_peaks
from typing import List
import pandas as pd
import numpy as np
import logging

log = logging.getLogger(__name__)

@dataclass
class RsiDivergenceProperties(ChartPatternProperties):
    min_periods_lapsed: int = 5 # minimum number of days to form a pattern
    min_change_pct: float = 0.005 # minimum change percentage

class RsiDivergencePattern:
    def __init__(self, points: List[Point], divergence_line: Line, is_high_pivots: bool):
        self.points = points
        self.divergence_line = divergence_line
        self.is_high_pivots = is_high_pivots

    def get_pattern_name_by_id(self, id: int) -> str:
        pattern_names = {
            1: "Bullish",
            2: "Bearish",
            3: "Hidden Bullish",
            4: "Hidden Bearish",
        }
        return pattern_names[id]

    def get_change_direction(self, value1: float, value2: float,
                             properties: RsiDivergenceProperties) -> int:
        change_pct = (value2 - value1) / value1
        if change_pct > properties.min_change_pct:
            return 1
        elif change_pct < -properties.min_change_pct:
            return -1
        return 0

    def resolve(self, properties: RsiDivergenceProperties) -> 'RsiDivergencePattern':
        if len(self.points) != 2:
            raise ValueError("Rsi Divergence must have 2 points")
        self.pattern_type = 0

        # makes prices always greater than the rsi values
        price_change_dir = self.get_change_direction(self.points[0].price,
            self.points[1].price, properties)
        rsi_change_dir = self.get_change_direction(self.divergence_line.p1.price,
            self.divergence_line.p2.price, properties)

        log.debug(f"points: {self.points[0].index}, {self.points[1].index}, "
                  f"rsi: {self.divergence_line.p1.price}, {self.divergence_line.p2.price}, "
                  f"price_change_dir: {price_change_dir}, rsi_change_dir: {rsi_change_dir}")

        if price_change_dir == 1 and rsi_change_dir == -1:
            if self.is_high_pivots:
                # higher high but lower RSI
                self.pattern_type = 2 # bearish
            else:
                # higher low but lower RSI
                self.pattern_type = 3 # hidden bullish
        elif price_change_dir == -1 and rsi_change_dir == 1:
            if self.is_high_pivots:
                # lower high but higher RSI
                self.pattern_type = 4 # hidden bearish
            else:
                # lower low but higher RSI
                self.pattern_type = 1 # bullish

        if self.pattern_type != 0:
            self.pattern_name = self.get_pattern_name_by_id(self.pattern_type)
        return self

def calc_rsi(prices: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate RSI"""
    series = prices["close"]
    ewm = dict(alpha=1.0 / period, min_periods=period, adjust=True, ignore_na=True)
    diff = series.diff()
    ups = diff.clip(lower=0).ewm(**ewm).mean()
    downs = diff.clip(upper=0).abs().ewm(**ewm).mean()

    return 100.0 - (100.0 / (1.0 + ups / downs))

def handle_rsi_pivots(rsi_pivots: pd.DataFrame, is_high_pivots: bool,
                      properties: RsiDivergenceProperties, patterns: List[RsiDivergencePattern]):
    if is_high_pivots:
        rsi_col = 'rsi_high'
        price_col = 'high'
    else:
        rsi_col = 'rsi_low'
        price_col = 'low'

    for i in range(len(rsi_pivots)-1):
        current_row = rsi_pivots.iloc[i]
        next_row = rsi_pivots.iloc[i+1]
        current_index = current_row['row_number'].astype(int)
        next_index = next_row['row_number'].astype(int)
        if next_index - current_index + 1 < properties.min_periods_lapsed:
            continue

        point1 = Point(current_row.name, current_index,
                       current_row[rsi_col])
        point2 = Point(next_row.name, next_index,
                       next_row[rsi_col])
        divergence_line = Line(point1, point2)
        price_points = [Point(current_row.name, current_index,
                       current_row[price_col]),
                 Point(next_row.name, next_index,
                       next_row[price_col])]
        pattern = RsiDivergencePattern(price_points, divergence_line, is_high_pivots).resolve(properties)
        if pattern.pattern_type != 0:
            patterns.append(pattern)

def find_rsi_divergences(backcandels: int, forwardcandels: int,
                         properties: RsiDivergenceProperties,
                         patterns: List[RsiDivergencePattern], df: pd.DataFrame):
    """
    Find RSI divergences using zigzag pivots

    Args:
        backcandels: Number of backcandels
        forwardcandels: Number of forwardcandels
        properties: RSI divergence properties
        patterns: List to store found patterns
        df: DataFrame with prices
    """
    # calculate rsi
    rsi = calc_rsi(df)
    # get rsi peaks
    rsi_highs, rsi_lows = window_peaks(rsi, backcandels, forwardcandels)
    rsi_high_pivots = rsi.where(rsi == rsi_highs)
    rsi_low_pivots = rsi.where(rsi == rsi_lows)
    # add row number
    df['row_number'] = pd.RangeIndex(len(df))

    # Merge for highs - including RSI values
    rsi_pivots= pd.merge(
        # Convert Series to DataFrame with column name
        pd.DataFrame({'rsi_high': rsi_high_pivots, 'rsi_low': rsi_low_pivots}),
        df[['row_number', 'high', 'low']],
        left_index=True,
        right_index=True,
        how='inner'
    )
    handle_rsi_pivots(rsi_pivots[['rsi_high', 'high','row_number']].dropna(), True, properties, patterns)
    handle_rsi_pivots(rsi_pivots[['rsi_low', 'low','row_number']].dropna(), False, properties, patterns)
