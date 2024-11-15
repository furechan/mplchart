import pytest
import pandas as pd
from mplchart.reversal_patterns import ReversalPattern, ReversalPatternProperties
from mplchart.line import Point, Line, Pivot

@pytest.fixture
def default_properties():
    return ReversalPatternProperties(
        min_periods_lapsed=5,
        flat_ratio=0.4,
    )

@pytest.fixture
def sample_pivots():
    """Create sample pivots for testing with slope calculations
    Slopes are calculated between pivots of the same direction:
    - For tops (direction=-1): slope between current top and previous top
    - For bottoms (direction=1): slope between current bottom and previous bottom
    """
    time_base = pd.Timestamp('2024-01-01')
    return [
        # First pivot (no previous pivot of same direction)
        Pivot(Point(index=0, time=time_base, price=100, norm_price=0.5), direction=-1, cross_diff=0.0),

        # First bottom (no previous bottom to calculate slope)
        Pivot(Point(index=2, time=time_base + pd.Timedelta(days=2), price=90, norm_price=0.40), direction=1, cross_diff=0.0),

        # Second top: cross_diff = 0.48-0.5 = -0.02
        Pivot(Point(index=4, time=time_base + pd.Timedelta(days=4), price=98, norm_price=0.48), direction=-1, cross_diff=-0.02),

        # Second bottom: cross_diff = 0.38-0.4 = -0.02
        Pivot(Point(index=6, time=time_base + pd.Timedelta(days=6), price=88, norm_price=0.38), direction=1, cross_diff=-0.02),

        # Third top: cross_diff = 0.49-0.48 = 0.01
        Pivot(Point(index=8, time=time_base + pd.Timedelta(days=8), price=99, norm_price=0.49), direction=-1, cross_diff=0.01)
    ]

def test_double_bottom_pattern(default_properties):
    """Test double bottom pattern identification with slope calculations"""
    time_base = pd.Timestamp('2024-01-01')
    pivots = [
        # First top (no previous top)
        Pivot(Point(index=0, time=time_base, price=100, norm_price=0.5), direction=1, cross_diff=0.0),

        # First bottom (no previous bottom)
        Pivot(Point(index=3, time=time_base + pd.Timedelta(days=2), price=90, norm_price=0.40), direction=-1, cross_diff=0.0),

        # Second top: cross_diff = 0.42-0.5 = -0.08
        Pivot(Point(index=4, time=time_base + pd.Timedelta(days=4), price=92, norm_price=0.42), direction=1, cross_diff=-0.08),

        # Second bottom: cross_diff = 0.41-0.4 = 0.01
        Pivot(Point(index=6, time=time_base + pd.Timedelta(days=6), price=91, norm_price=0.41), direction=-1, cross_diff=0.01),

        # Third top: cross_diff = 0.52-0.42 = 0.10
        Pivot(Point(index=8, time=time_base + pd.Timedelta(days=8), price=102, norm_price=0.52), direction=1, cross_diff=0.10)
    ]

    support_line = Line(
        Point(index=4, time=time_base + pd.Timedelta(days=4), price=90, norm_price=0.4),
        Point(index=4, time=time_base + pd.Timedelta(days=4), price=90, norm_price=0.4),
    )
    pattern = ReversalPattern(pivots, support_line)
    pattern = pattern.resolve(default_properties)

    assert pattern.pattern_type == 2  # Double Bottom
    assert pattern.get_pattern_name_by_id(pattern.pattern_type) == "Double Bottoms"

def test_head_and_shoulders_pattern(default_properties):
    """Test head and shoulders pattern identification with slope calculations"""
    time_base = pd.Timestamp('2024-01-01')
    pivots = [
        # First bottom (no previous bottom)
        Pivot(Point(index=0, time=time_base, price=90, norm_price=0.4), direction=-1, cross_diff=0.0),

        # First top (no previous top)
        Pivot(Point(index=2, time=time_base + pd.Timedelta(days=2), price=100, norm_price=0.50), direction=1, cross_diff=0.0),

        # Second bottom: cross_diff = 0.42-0.4 = -0.005
        Pivot(Point(index=4, time=time_base + pd.Timedelta(days=4), price=92, norm_price=0.42), direction=-1, cross_diff=-0.005),

        # Second top (head): cross_diff = 0.55-0.5 = 0.05
        Pivot(Point(index=6, time=time_base + pd.Timedelta(days=6), price=105, norm_price=0.55), direction=1, cross_diff=0.05),

        # Third bottom: cross_diff = 0.41-0.42 = -0.01
        Pivot(Point(index=8, time=time_base + pd.Timedelta(days=8), price=91, norm_price=0.41), direction=-1, cross_diff=-0.01),

        # Third top: cross_diff = 0.48-0.55 = -0.07
        Pivot(Point(index=10, time=time_base + pd.Timedelta(days=10), price=98, norm_price=0.48), direction=1, cross_diff=-0.07),

        # Fourth bottom: cross_diff = 0.47-0.41 = -0.06
        Pivot(Point(index=12, time=time_base + pd.Timedelta(days=12), price=97, norm_price=0.47), direction=-1, cross_diff=-0.06)
    ]

    support_line = Line(
        Point(index=4, time=time_base + pd.Timedelta(days=4), price=92, norm_price=0.42),
        Point(index=8, time=time_base + pd.Timedelta(days=8), price=91, norm_price=0.41)
    )
    pattern = ReversalPattern(pivots, support_line)
    pattern = pattern.resolve(default_properties)

    assert pattern.pattern_type == 5  # Head and Shoulders
    assert pattern.get_pattern_name_by_id(pattern.pattern_type) == "Head and Shoulders"
    # Verify head is higher than shoulders
    shoulder_highs = [p.point.norm_price for p in pattern.pivots if p.direction == 1 and p != pattern.pivots[3]]
    head_high = pattern.pivots[3].point.norm_price
    assert all(head_high > shoulder for shoulder in shoulder_highs)
