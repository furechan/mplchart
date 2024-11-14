from dataclasses import dataclass
from typing import List, Optional
import numpy as np
import pandas as pd

from .line import Pivot, Point

@dataclass
class ZigzagFlags:
    """Flags required for drawing zigzag"""
    new_pivot: bool = False
    double_pivot: bool = False
    update_last_pivot: bool = False

@dataclass
class Zigzag:
    def __init__(self, backcandels: int = 5, forwardcandels: int = 5,
                 pivot_limit: int = 20, offset: int = 0, level: int = 0):
        self.backcandels = backcandels
        self.forwardcandels = forwardcandels
        self.pivot_limit = pivot_limit
        self.offset = offset
        self.level = level
        self.zigzag_pivots: List[Pivot] = []
        self.flags = ZigzagFlags()

    def update_pivot_properties(self, pivot: Pivot) -> 'Zigzag':
        """
        Update the properties of the pivot
        """
        if len(self.zigzag_pivots) > 1:
            dir = np.sign(pivot.direction)
            value = pivot.point.norm_price
            last_pivot = self.zigzag_pivots[1]
            last_value = last_pivot.point.norm_price
            if last_pivot.point.index == pivot.point.index:
                raise ValueError(f"Last pivot index {last_pivot.point.index} is the same as current pivot index {pivot.point.index}")

            # Calculate difference between last and current pivot
            pivot.diff = round(abs(value - last_value), 3)

            if len(self.zigzag_pivots) > 2:
                llast_pivot = self.zigzag_pivots[2]
                llast_value = llast_pivot.point.norm_price
                # Calculate slope between last and current pivot
                pivot.cross_diff = round((value - llast_value), 3)
                # Determine if trend is strong (2) or weak (1)
                new_dir = dir * 2 if dir * value > dir * llast_value else dir
                pivot.direction = int(new_dir)

    def add_new_pivot(self, pivot: Pivot) -> 'Zigzag':
        """
        Add a new pivot to the zigzag

        Args:
            pivot: Pivot object to add

        Returns:
            self: Returns zigzag object for method chaining

        Raises:
            ValueError: If direction mismatch with last pivot
        """
        if len(self.zigzag_pivots) >= 1:
            # Check direction mismatch
            if np.sign(self.zigzag_pivots[0].direction) == np.sign(pivot.direction):
                raise ValueError('Direction mismatch')

        # Insert at beginning and maintain max size
        self.zigzag_pivots.insert(0, pivot)
        self.update_pivot_properties(pivot)

        if len(self.zigzag_pivots) > self.pivot_limit:
            print(f"Warning: pivots exceeded limit {self.pivot_limit}, popping pivot {self.zigzag_pivots[-1].point.index}")
            self.zigzag_pivots.pop()

        return self

    def window_peaks(self, df: pd.DataFrame, before: int, after: int) -> pd.Series:
        """
        Faster version using numpy's stride tricks

        Args:
            df: DataFrame with 'high' and 'low' columns
            before: Number of bars before the current bar
            after: Number of bars after the current bar

        Returns:
            pd.Series: Series of highs and lows
        """
        values_high = df["norm_high"].values
        values_low = df["norm_low"].values
        result_high = np.zeros(len(values_high))
        result_low = np.zeros(len(values_low))

        # Handle edges with padding
        padded_high = np.pad(values_high, (before, after), mode='edge')
        padded_low = np.pad(values_low, (before, after), mode='edge')

        # Create rolling window view
        windows_high = np.lib.stride_tricks.sliding_window_view(padded_high, before + after + 1)
        windows_low = np.lib.stride_tricks.sliding_window_view(padded_low, before + after + 1)
        result_high = np.max(windows_high, axis=1)
        result_low = np.min(windows_low, axis=1)

        return pd.Series(result_high, index=df.index), pd.Series(result_low, index=df.index)

    def calculate(self, df: pd.DataFrame, normalize: bool = True) -> 'Zigzag':
        """
        Calculate zigzag pivots from DataFrame

        Args:
            df: DataFrame with 'high' and 'low' columns
            normalize: Whether to normalize the prices

        Returns:
            self: Returns zigzag object for method chaining
        """
        # rescale the dataframe using the max and low prices in the range
        if df.get('norm_high') is None or df.get('norm_low') is None:
            if normalize:
                df = normalize_price(df)
            else:
                raise ValueError("Normalized prices not found in dataframe")

        self.zigzag_pivots = []
        self.flags = ZigzagFlags()

        highs, lows = self.window_peaks(df, self.backcandels, self.forwardcandels)

        # Calculate pivot highs
        pivot_highs = df['norm_high'].where((df['norm_high'] == highs))

        # Calculate pivot lows
        pivot_lows = df['norm_low'].where((df['norm_low'] == lows))

        # Process pivot points into zigzag
        last_pivot_price = None
        last_pivot_direction = 0

        for i in range(len(df)):
            if not (pd.isna(pivot_highs.iloc[i]) and pd.isna(pivot_lows.iloc[i])):
                current_index = i
                current_time = df.index[i]
                take_high = True
                if not pd.isna(pivot_highs.iloc[i]) and not pd.isna(pivot_lows.iloc[i]):
                    # both high and low pivot, take the more extreme one
                    if last_pivot_price is not None:
                        assert last_pivot_direction != 0
                        if last_pivot_direction == 1:
                            if pivot_highs.iloc[i] <= last_pivot_price:
                                # the current pivot high is lower than the last pivot high, take low instead
                                take_high = False
                        else:
                            if pivot_lows.iloc[i] < last_pivot_price:
                                # the current pivot low is lower than the last pivot low, take low instead
                                take_high = False
                elif pd.isna(pivot_highs.iloc[i]):
                    take_high = False

                if take_high:
                    current_norm_price = pivot_highs.iloc[i]
                    current_price = df.iloc[i]['high']
                    current_direction = 1 # bullish
                else:
                    current_norm_price = pivot_lows.iloc[i]
                    current_price = df.iloc[i]['low']
                    current_direction = -1 # bearish

                # Create and add pivot if valid
                if last_pivot_price is None or last_pivot_direction != current_direction:
                    new_pivot = Pivot(
                        point=Point(
                            price=current_price,
                            norm_price=current_norm_price,
                            index=current_index,
                            time=current_time
                        ),
                        direction=current_direction
                    )

                    self.add_new_pivot(new_pivot)
                    last_pivot_price = current_norm_price
                    last_pivot_direction = current_direction

                # Update last pivot if same direction but more extreme
                elif ((current_direction == 1 and current_norm_price > last_pivot_price) or
                    (current_direction == -1 and current_norm_price < last_pivot_price)):
                    # Update the last pivot
                    last_pivot = self.zigzag_pivots[0]
                    last_pivot.point.norm_price = current_norm_price
                    last_pivot.point.price = current_price
                    last_pivot.point.index = current_index
                    last_pivot.point.time = current_time
                    self.update_pivot_properties(last_pivot)
                    last_pivot_price = current_norm_price

        return self

    def get_pivot(self, index: int) -> Optional[Pivot]:
        """Get pivot at specific index"""
        if 0 <= index < len(self.zigzag_pivots):
            return self.zigzag_pivots[index]
        return None

    def get_last_pivot(self) -> Optional[Pivot]:
        """Get the most recent pivot"""
        return self.zigzag_pivots[0] if self.zigzag_pivots else None


def normalize_price(df: pd.DataFrame) -> pd.DataFrame:
    max_price = df['high'].max()
    min_price = df['low'].min() * 0.9
    df['norm_high'] = (df['high'] - min_price) / (max_price - min_price)
    df['norm_low'] = (df['low'] - min_price) / (max_price - min_price)
    df['norm_open'] = (df['open'] - min_price) / (max_price - min_price)
    df['norm_close'] = (df['close'] - min_price) / (max_price - min_price)
    return df