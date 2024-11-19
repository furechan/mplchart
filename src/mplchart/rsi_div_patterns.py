from dataclasses import dataclass
from mplchart.chart_pattern import ChartPatternProperties
from mplchart.line import Line, Point
from mplchart.zigzag import normalize_price, window_peaks
from typing import List
import pandas as pd
import numpy as np
import logging

log = logging.getLogger(__name__)

@dataclass
class RsiDivergenceProperties(ChartPatternProperties):
    min_periods_lapsed: int = 5 # minimum number of days to form a pattern
    flat_ratio: float = 0.005 # maximum allowed

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

    def resolve(self, properties: RsiDivergenceProperties) -> 'RsiDivergencePattern':
        if len(self.points) != 2:
            raise ValueError("Rsi Divergence must have 2 points")
        self.pattern_type = 0

        # makes prices always greater than the rsi values
        t1p1 = self.points[0].norm_price + 1
        t1p2 = self.points[1].norm_price + 1

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
        log.debug(f"points: {self.points[0].index}, {self.points[1].index}, "
                  f"rsi: {self.divergence_line.p1.norm_price}, {self.divergence_line.p2.norm_price}, "
                  f"upper_line_dir: {upper_line_dir}, lower_line_dir: {lower_line_dir}, "
                  f"upper_angle: {upper_angle}, lower_angle: {lower_angle}")

        if upper_line_dir == 1 and lower_line_dir == -1:
            if self.is_high_pivots:
                # higher high but lower RSI
                self.pattern_type = 2 # bearish
            else:
                # higher low but lower RSI
                self.pattern_type = 3 # hidden bullish
        elif upper_line_dir == -1 and lower_line_dir == 1:
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
        price_col = 'norm_high'
    else:
        rsi_col = 'rsi_low'
        price_col = 'norm_low'

    for i in range(len(rsi_pivots)-1):
        current_row = rsi_pivots.iloc[i]
        next_row = rsi_pivots.iloc[i+1]
        current_index = current_row['row_number'].astype(int)
        next_index = next_row['row_number'].astype(int)
        if next_index - current_index + 1 < properties.min_periods_lapsed:
            continue

        point1 = Point(current_row.name, current_index,
                       current_row[rsi_col], current_row[rsi_col] / 100)
        point2 = Point(next_row.name, next_index,
                       next_row[rsi_col], next_row[rsi_col] / 100)
        divergence_line = Line(point1, point2)
        price_points = [Point(current_row.name, current_index,
                       current_row[price_col], current_row[price_col]),
                 Point(next_row.name, next_index,
                       next_row[price_col], next_row[price_col])]
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
    # normalize prices
    prices = normalize_price(df)
    # calculate rsi
    rsi = calc_rsi(prices)
    # get rsi peaks
    rsi_highs, rsi_lows = window_peaks(rsi, backcandels, forwardcandels)
    rsi_high_pivots = rsi.where(rsi == rsi_highs)
    rsi_low_pivots = rsi.where(rsi == rsi_lows)
    # add row number
    prices['row_number'] = pd.RangeIndex(len(prices))

    # Merge for highs - including RSI values
    rsi_pivots= pd.merge(
        # Convert Series to DataFrame with column name
        pd.DataFrame({'rsi_high': rsi_high_pivots, 'rsi_low': rsi_low_pivots}),
        prices[['row_number', 'norm_high', 'norm_low']],
        left_index=True,
        right_index=True,
        how='inner'
    )
    handle_rsi_pivots(rsi_pivots[['rsi_high', 'norm_high','row_number']].dropna(), True, properties, patterns)
    handle_rsi_pivots(rsi_pivots[['rsi_low', 'norm_low','row_number']].dropna(), False, properties, patterns)
