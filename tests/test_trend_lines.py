import pytest
import pandas as pd
import numpy as np
from mplchart.trendlines import inspect_points, Point, ScanProperties

@pytest.fixture
def default_properties():
    return ScanProperties(
        error_ratio=1e-6,  # Very small error ratio
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
        'norm_open':  [0.2, 0.3, 0.25, 0.35, 0.4],
        'norm_high':  [0.25, 0.35, 0.3, 0.4, 0.45],
        'norm_low':   [0.15, 0.25, 0.2, 0.3, 0.35],
        'norm_close': [0.22, 0.28, 0.27, 0.38, 0.42]
    })

def test_perfectly_aligned_points(default_properties, sample_df):
    """Test points that form a perfect straight line"""
    points = [
        Point(index=0, time=pd.Timestamp('2024-01-01'), price=100, norm_price=0.2),
        Point(index=2, time=pd.Timestamp('2024-01-03'), price=110, norm_price=0.3),
        Point(index=4, time=pd.Timestamp('2024-01-05'), price=120, norm_price=0.4)
    ]

    valid, line = inspect_points(points, direction=1, properties=default_properties, df=sample_df)
    assert valid
    assert line is not None

def test_slightly_misaligned_points(default_properties, sample_df):
    """Test points that are slightly misaligned but within error ratio"""
    points = [
        Point(index=0, time=pd.Timestamp('2024-01-01'), price=100, norm_price=0.2),
        Point(index=2, time=pd.Timestamp('2024-01-03'), price=110.0001, norm_price=0.3),
        Point(index=4, time=pd.Timestamp('2024-01-05'), price=120, norm_price=0.4)
    ]

    valid, line = inspect_points(points, direction=1, properties=default_properties, df=sample_df)
    assert valid
    assert line is not None

def test_clearly_misaligned_points(default_properties, sample_df):
    """Test points that are clearly not aligned"""
    points = [
        Point(index=0, time=pd.Timestamp('2024-01-01'), price=100, norm_price=0.2),
        Point(index=2, time=pd.Timestamp('2024-01-03'), price=150, norm_price=0.5),  # Significant deviation
        Point(index=4, time=pd.Timestamp('2024-01-05'), price=120, norm_price=0.4)
    ]

    valid, line = inspect_points(points, direction=1, properties=default_properties, df=sample_df)
    assert not valid
    assert line is None

def test_two_points(default_properties, sample_df):
    """Test with only two points"""
    points = [
        Point(index=0, time=pd.Timestamp('2024-01-01'), price=100, norm_price=0.2),
        Point(index=2, time=pd.Timestamp('2024-01-03'), price=110, norm_price=0.3)
    ]

    valid, line = inspect_points(points, direction=1, properties=default_properties, df=sample_df)
    assert valid
    assert line is not None

def test_upper_trendline(default_properties, sample_df):
    """Test upper trendline validation against candle data"""
    points = [
        Point(index=0, time=pd.Timestamp('2024-01-01'), price=106, norm_price=0.26),  # Above high
        Point(index=2, time=pd.Timestamp('2024-01-03'), price=116, norm_price=0.36),  # Above high
        Point(index=4, time=pd.Timestamp('2024-01-05'), price=126, norm_price=0.46)   # Above high
    ]

    valid, line = inspect_points(points, direction=1, properties=default_properties, df=sample_df)
    assert valid
    assert line is not None

def test_lower_trendline(default_properties, sample_df):
    """Test lower trendline validation against candle data"""
    points = [
        Point(index=0, time=pd.Timestamp('2024-01-01'), price=94, norm_price=0.14),   # Below low
        Point(index=2, time=pd.Timestamp('2024-01-03'), price=104, norm_price=0.24),   # Below low
        Point(index=4, time=pd.Timestamp('2024-01-05'), price=114, norm_price=0.34)   # Below low
    ]

    valid, line = inspect_points(points, direction=-1, properties=default_properties, df=sample_df)
    assert valid
    assert line is not None

def test_invalid_upper_trendline(default_properties, sample_df):
    """Test invalid upper trendline that crosses candle bodies"""
    points = [
        Point(index=0, time=pd.Timestamp('2024-01-01'), price=101, norm_price=0.21),  # Crosses body
        Point(index=2, time=pd.Timestamp('2024-01-03'), price=106, norm_price=0.26),  # Crosses body
        Point(index=4, time=pd.Timestamp('2024-01-05'), price=121, norm_price=0.41)   # Crosses body
    ]

    valid, line = inspect_points(points, direction=1, properties=default_properties, df=sample_df)
    assert not valid
    assert line is None

def test_invalid_lower_trendline(default_properties, sample_df):
    """Test invalid lower trendline that crosses candle bodies"""
    points = [
        Point(index=0, time=pd.Timestamp('2024-01-01'), price=101, norm_price=0.21),  # Crosses body
        Point(index=2, time=pd.Timestamp('2024-01-03'), price=106, norm_price=0.26),  # Crosses body
        Point(index=4, time=pd.Timestamp('2024-01-05'), price=118, norm_price=0.38)   # Crosses body
    ]

    valid, line = inspect_points(points, direction=-1, properties=default_properties, df=sample_df)
    assert not valid
    assert line is None

def test_vertical_alignment(default_properties, sample_df):
    """Test points that are nearly vertical"""
    points = [
        Point(index=0, time=pd.Timestamp('2024-01-01'), price=100, norm_price=0.2),
        Point(index=0, time=pd.Timestamp('2024-01-01'), price=110, norm_price=0.3),  # Same index
        Point(index=1, time=pd.Timestamp('2024-01-02'), price=120, norm_price=0.4)
    ]

    valid, line = inspect_points(points, direction=1, properties=default_properties, df=sample_df)
    assert not valid  # Should fail due to vertical alignment
    assert line is None

def test_horizontal_alignment(default_properties, sample_df):
    """Test points that are nearly horizontal"""
    points = [
        Point(index=0, time=pd.Timestamp('2024-01-01'), price=120, norm_price=0.4),
        Point(index=2, time=pd.Timestamp('2024-01-03'), price=120.0001, norm_price=0.4),
        Point(index=4, time=pd.Timestamp('2024-01-05'), price=120.0002, norm_price=0.4)
    ]

    valid, line = inspect_points(points, direction=1, properties=default_properties, df=sample_df)
    assert valid  # Should work for horizontal lines
    assert line is not None