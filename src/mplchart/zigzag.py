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
        dir = np.sign(pivot.direction)
    
        if len(self.zigzag_pivots) >= 1:
            value = pivot.point.norm_price
            last_pivot = self.zigzag_pivots[0]
            last_value = last_pivot.point.norm_price
            last_index = last_pivot.point.index

             # Check direction mismatch
            if np.sign(last_pivot.direction) == np.sign(dir):
                raise ValueError('Direction mismatch')
                 
            # Calculate slope between last and current pivot
            pivot.ratio = round(
                (value - last_value) / (pivot.point.index - last_index), 
                3
            )
    
            if len(self.zigzag_pivots) >= 2:
                llast_pivot = self.zigzag_pivots[1]
                llast_value = llast_pivot.point.norm_price
                 
                # Determine if trend is strong (2) or weak (1)
                new_dir = dir * 2 if dir * value > dir * llast_value else dir
                pivot.direction = int(new_dir)
                
        # Insert at beginning and maintain max size
        self.zigzag_pivots.insert(0, pivot)
        if len(self.zigzag_pivots) > self.pivot_limit:
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
    
    def calculate(self, df: pd.DataFrame) -> 'Zigzag':
        """
        Calculate zigzag pivots from DataFrame
        
        Args:
            df: DataFrame with 'high' and 'low' columns
            
        Returns:
            self: Returns zigzag object for method chaining
        """
        # rescale the dataframe using the max and low prices in the range
        max_price = df['high'].max()
        min_price = df['low'].min() * 0.9
        df['norm_high'] = (df['high'] - min_price) / (max_price - min_price)
        df['norm_low'] = (df['low'] - min_price) / (max_price - min_price)
        df['norm_open'] = (df['open'] - min_price) / (max_price - min_price)
        df['norm_close'] = (df['close'] - min_price) / (max_price - min_price)
 
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
                
                if not pd.isna(pivot_highs.iloc[i]) and not pd.isna(pivot_lows.iloc[i]):
                    # Both high and low pivot - take the more extreme one
                    if last_pivot_price is not None:
                        high_change = abs(pivot_highs.iloc[i] - last_pivot_price)
                        low_change = abs(pivot_lows.iloc[i] - last_pivot_price)
                        if high_change > low_change:
                            current_norm_price = pivot_highs.iloc[i]
                            current_price = df.iloc[i]['high']
                            # 1 for bullish, -1 for bearish
                            current_direction = 1
                        else:
                            current_norm_price = pivot_lows.iloc[i]
                            current_price = df.iloc[i]['low']
                            current_direction = -1
                    else:
                        # First pivot - take the high
                        current_norm_price = pivot_highs.iloc[i]
                        current_price = df.iloc[i]['high']
                        current_direction = 1
                
                elif not pd.isna(pivot_highs.iloc[i]):
                    current_norm_price = pivot_highs.iloc[i]
                    current_price = df.iloc[i]['high']
                    current_direction = 1
                else:
                    current_norm_price = pivot_lows.iloc[i]
                    current_price = df.iloc[i]['low']
                    current_direction = -1
                
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
                    
                    try:
                        self.add_new_pivot(new_pivot)
                        last_pivot_price = current_norm_price
                        last_pivot_direction = current_direction
                    except ValueError:
                        # Handle case where pivot couldn't be added
                        continue
                
                # Update last pivot if same direction but more extreme
                elif ((current_direction == 1 and current_norm_price > last_pivot_price) or
                    (current_direction == -1 and current_norm_price < last_pivot_price)):
                    # Update the last pivot
                    self.zigzag_pivots[0].point.norm_price = current_norm_price
                    self.zigzag_pivots[0].point.price = current_price
                    self.zigzag_pivots[0].point.index = current_index
                    self.zigzag_pivots[0].point.time = current_time
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

    def nextlevel(self) -> 'Zigzag':
        """
        Calculate Next Level Zigzag based on the current calculated zigzag object
        
        Returns:
            Zigzag: Next level zigzag object
        """
        # Create new zigzag object for next level
        next_level = Zigzag(
            length=self.length,
            pivot_limit=self.pivot_limit,
            offset=0
        )
        next_level.level = self.level + 1
        
        # Process only if we have pivots
        if len(self.zigzag_pivots) > 0:
            temp_bullish_pivot: Optional[Pivot] = None
            temp_bearish_pivot: Optional[Pivot] = None
            
            # Process pivots from oldest to newest
            for i in range(len(self.zigzag_pivots) - 1, -1, -1):
                # Create copy of current pivot and adjust level
                l_pivot = Pivot.deep_copy(self.zigzag_pivots[i])
                dir = l_pivot.direction
                new_dir = np.sign(dir)
                value = l_pivot.point.price
                l_pivot.level = l_pivot.level + 1
                
                if len(next_level.zigzag_pivots) > 0:
                    last_pivot = next_level.zigzag_pivots[0]
                    last_dir = np.sign(last_pivot.direction)
                    last_value = last_pivot.point.price
                
                    if abs(dir) == 2:  # Strong trend
                        if last_dir == new_dir:
                            if dir * last_value < dir * value:
                                next_level.zigzag_pivots.pop(0)
                            else:
                                temp_pivot = (temp_bearish_pivot if new_dir > 0 
                                            else temp_bullish_pivot)
                                if temp_pivot is not None:
                                    next_level.add_new_pivot(temp_pivot)
                                else:
                                    continue
                        else:
                            temp_first_pivot = (temp_bullish_pivot if new_dir > 0 
                                              else temp_bearish_pivot)
                            temp_second_pivot = (temp_bearish_pivot if new_dir > 0 
                                               else temp_bullish_pivot)

                            if (temp_first_pivot is not None and 
                                temp_second_pivot is not None):
                                temp_val = temp_first_pivot.point.price
                                val = l_pivot.point.price

                                if new_dir * temp_val > new_dir * val:
                                    next_level.add_new_pivot(temp_first_pivot)
                                    next_level.add_new_pivot(temp_second_pivot)

                        next_level.add_new_pivot(l_pivot)
                        temp_bullish_pivot = None
                        temp_bearish_pivot = None
                    
                    else:  # Weak trend
                        temp_pivot = (temp_bullish_pivot if new_dir > 0 
                                    else temp_bearish_pivot)

                        if temp_pivot is not None:
                            temp_dir = temp_pivot.direction
                            temp_val = temp_pivot.point.price
                            val = l_pivot.point.price

                            if val * dir > temp_val * dir:
                                if new_dir > 0:
                                    temp_bullish_pivot = l_pivot
                                else:
                                    temp_bearish_pivot = l_pivot
                        else:
                            if new_dir > 0:
                                temp_bullish_pivot = l_pivot
                            else:
                                temp_bearish_pivot = l_pivot
                            
                elif abs(dir) == 2:  # First pivot and strong trend
                    next_level.add_new_pivot(l_pivot)
        
            # Clear if we didn't reduce the number of pivots
            if len(next_level.zigzag_pivots) >= len(self.zigzag_pivots):
                next_level.zigzag_pivots.clear()
            
        return next_level
