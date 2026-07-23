"""Tests for the OHLC settings hook."""

import pytest
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from mplchart.chart import Chart
from mplchart.primitives import OHLC
from mplchart.styles import Styler

pd = pytest.importorskip("pandas")


def make_prices():
    """Two bars: first counts as up (no previous close), second closes down."""
    return pd.DataFrame(
        {
            "open": [10.0, 10.5],
            "high": [11.5, 12.0],
            "low": [9.5, 10.0],
            "close": [11.0, 10.5],
            "volume": [100, 100],
        },
        index=pd.date_range("2024-01-01", periods=2, freq="D"),
    )


def plot_bars(settings=(), style=None, **kwargs):
    """Plot and return the bars PolyCollection; caller closes the figure."""
    chart = Chart(make_prices(), figsize=(4, 3), style=style or Styler(settings=settings))
    chart.plot(OHLC(**kwargs))
    (poly,) = chart.canvas.main_axes().collections
    return chart.figure, poly


def rgba(color):
    return mcolors.to_rgba(color)


def test_default_mono():
    fig, poly = plot_bars()
    textcolor = rgba(plt.rcParams["text.color"])
    assert [tuple(c) for c in poly.get_edgecolor()] == [textcolor] * 2
    plt.close(fig)


def test_color_kwargs():
    fig, poly = plot_bars(colorup="green", colordn="red")
    assert [tuple(c) for c in poly.get_edgecolor()] == [rgba("green"), rgba("red")]
    plt.close(fig)


def test_settings_colors():
    scheme = {"ohlc.up.color": "green", "ohlc.down.color": "red"}
    fig, poly = plot_bars(settings=scheme)
    assert [tuple(c) for c in poly.get_edgecolor()] == [rgba("green"), rgba("red")]
    plt.close(fig)


def test_kwargs_override_per_side():
    # side colors are independent params — a kwarg overrides only its own side
    scheme = {"ohlc.down.color": "blue"}
    fig, poly = plot_bars(settings=scheme, colorup="green")
    assert [tuple(c) for c in poly.get_edgecolor()] == [rgba("green"), rgba("blue")]
    plt.close(fig)


def test_settings_alpha():
    style = Styler(settings={"ohlc.alpha": 0.25})
    fig, poly = plot_bars(style=style)
    assert poly.get_alpha() == 0.25
    plt.close(fig)

    # explicit kwarg wins over the setting
    fig, poly = plot_bars(style=style, alpha=0.75)
    assert poly.get_alpha() == 0.75
    plt.close(fig)


def test_shipped_style_colors_ohlc():
    fig, poly = plot_bars(style="nightclouds")
    assert [tuple(c) for c in poly.get_edgecolor()] == [rgba("white"), rgba("#4a90d9")]
    plt.close(fig)
