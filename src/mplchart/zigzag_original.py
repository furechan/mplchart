from dataclasses import dataclass
from typing import List, Optional
import numpy as np
import pandas as pd

from .line import Pivot, Point

@dataclass
class PivotCandle:
    """Represents data of the candle which forms either pivot High or pivot low or both
    
    Attributes:
        high: High price of candle forming the pivot
        low: Low price of candle forming the pivot
        length: Pivot length
        p_high_bar: Number of bars back the pivot High occurred
        p_low_bar: Number of bars back the pivot Low occurred
        p_high: Pivot High Price
        p_low: Pivot Low Price
    """
    high: float
    low: float
    length: int = 5
    p_high_bar: int = 0
    p_low_bar: int = 0
    p_high: float = 0.0
    p_low: float = 0.0
    
    def init(self, df: pd.DataFrame, offset: int) -> 'PivotCandle':
        """Create PivotCandle from DataFrame
        
        Args:
            df: DataFrame with high/low columns
            length: Lookback period length
            
        Returns:
            PivotCandle object initialized from DataFrame
        """
        end_idx = len(df) - offset
        start_idx = max(0, end_idx - self.length)

        window = df['high'].iloc[start_idx:end_idx]
        self.p_high_bar = start_idx + window.values.argmax()
        self.p_high = window.max()
        
        window = df['low'].iloc[start_idx:end_idx]
        self.p_low_bar = start_idx + window.values.argmin()
        self.p_low = window.min()

        return self

@dataclass
class ZigzagFlags:
    """Flags required for drawing zigzag"""
    new_pivot: bool = False
    double_pivot: bool = False
    update_last_pivot: bool = False

@dataclass
class Zigzag:
    def __init__(self, length: int = 5, number_of_pivots: int = 20, 
                 offset: int = 0, level: int = 0):
        self.length = length
        self.number_of_pivots = number_of_pivots
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
            last_pivot = self.zigzag_pivots[0]
            last_value = last_pivot.point.price
             
             # Check direction mismatch
            if np.sign(last_pivot.direction) == np.sign(dir):
                raise ValueError('Direction mismatch')
                 
            if len(self.zigzag_pivots) >= 2:
                llast_pivot = self.zigzag_pivots[1]
                value = pivot.point.price
                llast_value = llast_pivot.point.price
                 
                # Determine if trend is strong (2) or weak (1)
                new_dir = dir * 2 if dir * value > dir * llast_value else dir
                pivot.direction = int(new_dir)
                
                # Calculate price ratio
                pivot.ratio = round(
                    abs(last_value - value) / abs(llast_value - last_value), 
                    3
                )
                
                # Calculate bar ratio
                pivot.bar_ratio = round(
                    abs(last_pivot.point.index - pivot.point.index) / 
                    abs(llast_pivot.point.index - last_pivot.point.index),
                    3
                )
                
                if len(self.zigzag_pivots) >= 3:
                    lllast_pivot = self.zigzag_pivots[2]
                    lllast_value = lllast_pivot.point.price
                    
                    # Calculate size ratio
                    pivot.size_ratio = round(
                        abs(last_value - value) / abs(lllast_value - llast_value),
                        3
                    )
    
        # Insert at beginning and maintain max size
        self.zigzag_pivots.insert(0, pivot)
        if len(self.zigzag_pivots) > self.number_of_pivots:
            self.zigzag_pivots.pop()
            
        return self

    def calculate(self, df: pd.DataFrame) -> 'Zigzag':
        for i in range(self.offset, len(df)):
            self.find_pivot(df, i)
        return self
    
    def find_pivot(self, df: pd.DataFrame, offset: int = 0) -> 'Zigzag':
        # Get current row considering offset
        if offset < 0 or offset >= len(df):
            raise ValueError(f"Offset {offset} is out of bounds")
        
        current_row = df.iloc[-1-offset]
        current_time = df.index[-1-offset]
    
        # Create and initialize candle object using current OHLC data
        candle = PivotCandle(
            high=current_row['high'],
            low=current_row['low'],
            length=self.length
        ).init(df, offset)
    
        p_dir = 1
        last_pivot = None
        self.flags.update_last_pivot = False
        self.flags.new_pivot = False 
        self.flags.double_pivot = False
    
        # Use DataFrame index as bar reference
        new_bar = len(df) - 1 - offset
        distance_from_last_pivot = 0
        force_double_pivot = False

        # Get last pivot if exists
        if len(self.zigzag_pivots) > 0:
            last_pivot = self.zigzag_pivots[0]
            p_dir = int(np.sign(last_pivot.direction))
            distance_from_last_pivot = new_bar - last_pivot.point.index

        # Check for force double pivot condition
        if len(self.zigzag_pivots) > 1:
            llast_pivot = self.zigzag_pivots[1]
            
            if p_dir == 1 and candle.p_low_bar == 0:
                force_double_pivot = candle.p_low < llast_pivot.point.price
            elif p_dir == -1 and candle.p_high_bar == 0:
                force_double_pivot = candle.p_high > llast_pivot.point.price
            else:
                force_double_pivot = False

        overflow = distance_from_last_pivot >= self.length

        # Handle pivot updates
        if ((p_dir == 1 and candle.p_high_bar == 0) or 
            (p_dir == -1 and candle.p_low_bar == 0)) and len(self.zigzag_pivots) >= 1:
            
            value = candle.p_high if p_dir == 1 else candle.p_low
            
            remove_old = value * last_pivot.direction >= last_pivot.point.price * last_pivot.direction
            
            if remove_old:
                self.flags.update_last_pivot = True
                self.flags.new_pivot = True
                self.zigzag_pivots.pop(0)
                new_pivot_object = Pivot(
                    point=Point(index=new_bar, price=value, time=current_time),
                    direction=p_dir
                )
                self.add_new_pivot(new_pivot_object)

        # Handle new pivot creation
        if ((p_dir == 1 and candle.p_low_bar == 0) or 
            (p_dir == -1 and candle.p_high_bar == 0)) and (not self.flags.new_pivot or force_double_pivot):
            
            value = candle.p_low if p_dir == 1 else candle.p_high
            
            new_pivot_object = Pivot(
                point=Point(index=new_bar, price=value, time=current_time),
                direction=-p_dir
            )
            self.add_new_pivot(new_pivot_object)
            self.flags.double_pivot = self.flags.new_pivot
            self.flags.new_pivot = True

        # Handle overflow condition
        if overflow and not self.flags.new_pivot:
            ipivot = candle.p_low if p_dir == 1 else candle.p_high
            ipivot_bar = new_bar + (candle.p_low_bar if p_dir == 1 else candle.p_high_bar)
            
            # Get time from the correct offset in the DataFrame
            offset_idx = new_bar - ipivot_bar + self.offset
            ipivot_time = df.index[offset_idx]

            new_pivot_object = Pivot(
                point=Point(index=ipivot_bar, price=ipivot, time=ipivot_time),
                direction=-p_dir
            )
            self.add_new_pivot(new_pivot_object)
            self.flags.new_pivot = True

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
            number_of_pivots=self.number_of_pivots,
            offset=0
        )
        next_level.level = self.level + 1
        next_level.init()
        
        # Process only if we have pivots
        if len(self.zigzag_pivots) > 0:
            temp_bullish_pivot: Optional[Pivot] = None
            temp_bearish_pivot: Optional[Pivot] = None
            
            # Process pivots from oldest to newest
            for i in range(len(self.zigzag_pivots) - 1, -1, -1):
                # Create copy of current pivot and adjust level
                l_pivot = Pivot.copy(self.zigzag_pivots[i])
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
