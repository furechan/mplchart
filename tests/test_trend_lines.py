import pytest
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

from mplchart.trendlines import inspect_line
from mplchart.line import Line, Point

def create_test_df(prices: list) -> pd.DataFrame:
    """Helper function to create test DataFrame"""
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(len(prices))]
    return pd.DataFrame({
        'open': [p + random.random() - 0.5 for p in prices],
        'high': [p + 1 for p in prices],
        'low': [p - 1 for p in prices],
        'close': [p + random.random() - 0.5 for p in prices]
    }, index=dates)

def test_inspect_line_basic_uptrend():
    """Test basic uptrend line inspection"""
    # Create test data
    df = create_test_df([100, 101, 102, 103, 104])
    
    # Create uptrend line
    line = Line(
        Point(time=df.index[0], index=0, price=101),
        Point(time=df.index[4], index=4, price=105)
    )
    
    plot_test_data("Basic Uptrend Test", line, df)
    # Test inspection
    valid, score = inspect_line(line, 0, 4, 2, 1, df)
    assert valid == True
    assert score > 0

def test_inspect_line_basic_downtrend():
    """Test basic downtrend line inspection"""
    # Create test data
    df = create_test_df([104, 103, 102, 101, 100])
    
    # Create downtrend line
    line = Line(
        Point(time=df.index[0], index=0, price=103),
        Point(time=df.index[4], index=4, price=99)
    )
    plot_test_data("Basic Downtrend Test", line, df)

    # Test inspection
    valid, score = inspect_line(line, 0, 4, 2, -1, df)
    assert valid == True
    assert score > 0

def test_inspect_line_invalid_break():
    """Test line becomes invalid when price breaks through"""
    # Create test data with a break
    df = create_test_df([100, 101, 95, 103, 104])  # Break at index 2
    
    # Create uptrend line
    line = Line(
        Point(time=df.index[0], index=0, price=99),
        Point(time=df.index[4], index=4, price=103)
    )
    
    plot_test_data("Invalid Break Test", line, df)
    
    # Test inspection
    valid, score = inspect_line(line, 0, 4, 3, 1, df)
    assert valid == False

def test_inspect_line_at_other_bar():
    """Test line becomes invalid when breaking at other_bar"""
    # Create test data
    df = create_test_df([100, 101, 102, 103, 104])
    
    # Create line that breaks at other_bar
    line = Line(
        Point(time=df.index[0], index=0, price=99),
        Point(time=df.index[4], index=4, price=105)
    )
    
    plot_test_data("Line Breaks at Other Bar Test", line, df)
    
    # Test inspection with other_bar at index 2
    valid, score = inspect_line(line, 0, 4, 2, 1, df)
    assert valid == False

def test_inspect_line_no_df():
    """Test inspection with no DataFrame provided"""
    line = Line(
        Point(time=0, index=0, price=100),
        Point(time=4, index=4, price=104)
    )
    
    valid, score = inspect_line(line, 0, 4, 2, 1)
    assert valid == True
    assert score == 0

def test_inspect_line_df_too_short():
    """Test inspection with DataFrame shorter than range"""
    df = create_test_df([100, 101])  # Only 2 bars
    
    line = Line(
        Point(time=df.index[0], index=0, price=100),
        Point(time=df.index[1], index=4, price=104)  # Goes beyond df length
    )
    
    valid, score = inspect_line(line, 0, 4, 2, 1, df)
    assert valid == True  # Should still be valid
    assert score < 5  # Should only score available bars

def test_inspect_line_edge_cases():
    """Test various edge cases"""
    df = create_test_df([100, 100, 100, 100, 100])  # Flat prices
    
    # Test horizontal line
    horizontal_line = Line(
        Point(time=df.index[0], index=0, price=100),
        Point(time=df.index[4], index=4, price=100)
    )
    plot_test_data("Edge Case: Horizontal Line", horizontal_line, df)
    valid, score = inspect_line(horizontal_line, 0, 4, 2, 1, df)
    assert valid == True
    
    # Test single-bar inspection
    valid, score = inspect_line(horizontal_line, 2, 2, 2, 1, df)
    assert valid == True
    assert score <= 1
    
    # Test invalid indices
    with pytest.raises(IndexError):
        inspect_line(horizontal_line, -10, 4, 2, 1, df)

def test_inspect_line_direction_handling():
    """Test how different directions are handled"""
    df = create_test_df([100, 101, 102, 103, 104])
    
    line = Line(
        Point(time=df.index[0], index=0, price=100),
        Point(time=df.index[4], index=4, price=104)
    )
    
    plot_test_data("Direction Handling Test", line, df)
    
    # Test upward direction
    valid_up, score_up = inspect_line(line, 0, 4, 2, 1, df)
    assert valid_up == True
    
    # Test downward direction (should fail for this upward line)
    valid_down, score_down = inspect_line(line, 0, 4, 2, -1, df)
    assert valid_down == False
    

def plot_test_data(title: str, line: Line, df: pd.DataFrame):
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot candlesticks
    width = 0.6
    
    for idx, row in df.iterrows():
        # Plot candle body
        color = 'g' if row['close'] >= row['open'] else 'r'
        bottom = min(row['open'], row['close'])
        height = abs(row['close'] - row['open'])
        ax.bar(idx, height, width, bottom=bottom, color=color)
        
        # Plot wicks
        ax.plot([idx, idx], [row['low'], row['high']], color='black', linewidth=1)
    
    # Plot trend line
    ax.plot([df.index[0], df.index[4]], 
            [line.p1.price, line.p2.price], 
            'r--', 
            label='Trend Line',
            linewidth=2)
    
    # Customize plot
    ax.set_title(title)
    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend()
    
    # Format x-axis
    ax.set_xticks(df.index)
    ax.set_xticklabels([d.strftime('%Y-%m-%d') for d in df.index], 
                       rotation=45)
    
    # Set y-axis limits with some padding
    price_range = df['high'].max() - df['low'].min()
    ax.set_ylim(df['low'].min() - price_range*0.1, 
                df['high'].max() + price_range*0.1)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save plot
    plt.savefig(title + '_matplotlib.png')
    plt.close()