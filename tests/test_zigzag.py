import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from mplchart.zigzag import Zigzag, Pivot, Point

def calculate_with_rolling_window():
    """Test zigzag calculation using rolling windows"""
    # Create sample data with clear pivot points
    data = {
        'high': [10, 11, 12, 11, 10, 11, 13, 12, 11],
        'low':  [9, 10, 11, 9, 8, 10, 12, 10, 9]
    }
    df = pd.DataFrame(data, index=pd.date_range('2024-01-01', periods=len(data['high'])))
    
    zigzag = Zigzag(backcandels=2, forwardcandels=4)
    zigzag.calculate(df)
    
    # Verify pivots
    assert len(zigzag.zigzag_pivots) > 0
    
    # Check first pivot (should be high)
    first_pivot = zigzag.zigzag_pivots[-1]
    assert first_pivot.direction == 1
    assert first_pivot.point.price == 12  # Local high
    
    # Check second pivot (should be low)
    second_pivot = zigzag.zigzag_pivots[-2]
    assert second_pivot.direction == -1
    assert  second_pivot.point.price == 8  # Local low

def test_window_peaks():
    """Test window peaks calculation"""
    data = {
        'high': [10, 11, 12, 11, 10, 11, 13, 12, 11, 9],
        'low':  [9, 10, 11, 9, 8, 10, 12, 10, 9, 7]
    }
    df = pd.DataFrame(data, index=pd.date_range('2024-01-01', periods=len(data['high'])))
    
    zigzag = Zigzag(backcandels=2, forwardcandels=4)
    highs, lows = zigzag.window_peaks(df, 2, 4)
    assert highs.values.tolist() == [12, 12, 13, 13, 13, 13, 13, 13, 13, 12]
    assert lows.values.tolist() == [8, 8, 8, 8, 8, 7, 7, 7, 7, 7]
