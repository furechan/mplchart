import pytest
import pandas as pd
import numpy as np
from mplchart.trendline_patterns import Pivot, TrendLineProperties, Point, is_aligned

@pytest.fixture
def default_properties():
    return TrendLineProperties(
        align_ratio=0.2,
        flat_ratio=0.2,
        flag_ratio=0.8
    )

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        'open':  [100, 110, 105, 115, 120],
        'high':  [105, 115, 110, 120, 125],
        'low':   [95,  105, 100, 110, 115],
        'close': [102, 108, 107, 118, 122],
    })

def test_aligned_pivots(default_properties, sample_df):
    """Test pivots that are properly aligned"""
    pivots = [
        Pivot(point=Point(index=0, time=pd.Timestamp('2024-01-01'), price=100), direction=1, diff=0, cross_diff=0),
        Pivot(point=Point(index=2, time=pd.Timestamp('2024-01-03'), price=110), direction=1, diff=5, cross_diff=10),
        Pivot(point=Point(index=4, time=pd.Timestamp('2024-01-05'), price=120), direction=1, diff=5, cross_diff=10)
    ]

    ref_pivots = [
        Pivot(point=Point(index=1, time=pd.Timestamp('2024-01-02'), price=105), direction=-1, diff=0, cross_diff=0),
        Pivot(point=Point(index=3, time=pd.Timestamp('2024-01-04'), price=115), direction=-1, diff=5, cross_diff=10)
    ]

    assert is_aligned(pivots, ref_pivots, default_properties.align_ratio, default_properties.flat_ratio)

def test_flat_aligned_pivots(default_properties, sample_df):
    """Test pivots that are aligned horizontally"""
    pivots = [
        Pivot(point=Point(index=0, time=pd.Timestamp('2024-01-01'), price=100), direction=1, diff=0, cross_diff=0),
        Pivot(point=Point(index=2, time=pd.Timestamp('2024-01-03'), price=100), direction=1, diff=10, cross_diff=0),
        Pivot(point=Point(index=4, time=pd.Timestamp('2024-01-05'), price=100), direction=1, diff=10, cross_diff=0)
    ]

    ref_pivots = [
        Pivot(point=Point(index=1, time=pd.Timestamp('2024-01-02'), price=90), direction=-1, diff=-10, cross_diff=0),
        Pivot(point=Point(index=3, time=pd.Timestamp('2024-01-04'), price=90), direction=-1, diff=-10, cross_diff=0)
    ]

    assert is_aligned(pivots, ref_pivots, default_properties.align_ratio, default_properties.flat_ratio)

def test_misaligned_pivots(default_properties, sample_df):
    """Test pivots that are not aligned"""
    pivots = [
        Pivot(point=Point(index=0, time=pd.Timestamp('2024-01-01'), price=100), direction=1, diff=0, cross_diff=0),
        Pivot(point=Point(index=2, time=pd.Timestamp('2024-01-03'), price=120), direction=1, diff=30, cross_diff=20),
        Pivot(point=Point(index=4, time=pd.Timestamp('2024-01-05'), price=130), direction=1, diff=40, cross_diff=10)
    ]

    ref_pivots = [
        Pivot(point=Point(index=1, time=pd.Timestamp('2024-01-02'), price=90), direction=-1, diff=-10, cross_diff=0),
        Pivot(point=Point(index=3, time=pd.Timestamp('2024-01-04'), price=90), direction=-1, diff=-30, cross_diff=0)
    ]

    assert not is_aligned(pivots, ref_pivots, default_properties.align_ratio, default_properties.flat_ratio)

def test_wrong_direction_pivots(default_properties, sample_df):
    """Test pivots with inconsistent directions"""
    pivots = [
        Pivot(point=Point(index=0, time=pd.Timestamp('2024-01-01'), price=100), direction=1, diff=0, cross_diff=0),
        Pivot(point=Point(index=2, time=pd.Timestamp('2024-01-03'), price=110), direction=-1, diff=5, cross_diff=10),
        Pivot(point=Point(index=4, time=pd.Timestamp('2024-01-05'), price=120), direction=1, diff=5, cross_diff=10)
    ]

    ref_pivots = [
        Pivot(point=Point(index=1, time=pd.Timestamp('2024-01-02'), price=105), direction=-1, diff=5, cross_diff=0),
        Pivot(point=Point(index=3, time=pd.Timestamp('2024-01-04'), price=115), direction=-1, diff=5, cross_diff=10)
    ]

    with pytest.raises(ValueError, match="Pivots must have the same direction"):
        is_aligned(pivots, ref_pivots, default_properties.align_ratio, default_properties.flat_ratio)

def test_too_many_pivots(default_properties, sample_df):
    """Test with more than 3 pivots"""
    pivots = [
        Pivot(point=Point(index=0, time=pd.Timestamp('2024-01-01'), price=100), direction=1, diff=0, cross_diff=0),
        Pivot(point=Point(index=1, time=pd.Timestamp('2024-01-02'), price=110), direction=1, diff=10, cross_diff=0),
        Pivot(point=Point(index=2, time=pd.Timestamp('2024-01-03'), price=120), direction=1, diff=10, cross_diff=20),
        Pivot(point=Point(index=3, time=pd.Timestamp('2024-01-04'), price=130), direction=1, diff=10, cross_diff=20)
    ]

    ref_pivots = []

    with pytest.raises(ValueError, match="Pivots can't be more than 3"):
        is_aligned(pivots, ref_pivots, default_properties.align_ratio, default_properties.flat_ratio)