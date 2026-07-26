"""Tests for the Volume settings hook."""

import pytest
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from mplchart.chart import Chart
from mplchart.colors import closest_color
from mplchart.primitives import Volume
from mplchart.styles import Styler

pd = pytest.importorskip("pandas")


def make_prices():
    """Two bars: intrabar up then intrabar down (interbar would say up)."""
    return pd.DataFrame(
        {
            "open": [10.0, 12.0],
            "high": [12.0, 12.5],
            "low": [9.5, 11.0],
            "close": [11.0, 11.5],  # bar 1 closes above prev close but below its open
            "volume": [100, 150],
        },
        index=pd.date_range("2024-01-01", periods=2, freq="D"),
    )


def plot_volume(settings=(), style=None, **kwargs):
    """Plot and return the volume-bars PolyCollection; caller closes the figure."""
    chart = Chart(make_prices(), figsize=(4, 3), style=style or Styler(settings=settings))
    chart.plot(Volume(**kwargs))
    # volume-only chart: Volume owns the main pane outright (no twin)
    (poly,) = chart.canvas.main_axes().collections
    return chart.figure, poly


def rgba(color):
    return mcolors.to_rgba(color)


def rgb(colors):
    """RGB triples of a facecolor array — collection alpha bakes into RGBA."""
    return [tuple(c)[:3] for c in colors]


def test_default_snapped_colors_intrabar():
    # defaults snap to the prop cycle; direction is intrabar (bar 1 is down)
    fig, poly = plot_volume()
    green, red = rgba(closest_color("green")), rgba(closest_color("red"))
    assert rgb(poly.get_facecolor()) == [green[:3], red[:3]]
    plt.close(fig)


def test_color_kwargs_exact():
    # explicit kwargs are exact — no prop-cycle snapping (unlike the defaults)
    teal = "#26a69a"
    fig, poly = plot_volume(colorup=teal, colordn="red")
    assert rgb(poly.get_facecolor())[0] == rgba(teal)[:3]
    plt.close(fig)


def test_settings_colors():
    scheme = {"volume.up.color": "green", "volume.down.color": "blue"}
    fig, poly = plot_volume(settings=scheme)
    assert rgb(poly.get_facecolor()) == [rgba("green")[:3], rgba("blue")[:3]]
    plt.close(fig)


def test_kwargs_override_per_side():
    # independent per-element params — a kwarg overrides only its own setting
    scheme = {"volume.down.color": "blue"}
    fig, poly = plot_volume(settings=scheme, colorup="green")
    assert rgb(poly.get_facecolor()) == [rgba("green")[:3], rgba("blue")[:3]]
    plt.close(fig)


def test_settings_alpha():
    style = Styler(settings={"volume.alpha": 0.25})
    fig, poly = plot_volume(style=style)
    assert poly.get_alpha() == 0.25
    plt.close(fig)

    # explicit kwarg wins over the setting
    fig, poly = plot_volume(style=style, alpha=0.75)
    assert poly.get_alpha() == 0.75
    plt.close(fig)


def test_settings_ma_color():
    scheme = {"volume.ma.color": "purple"}
    chart = Chart(make_prices(), figsize=(4, 3), style=Styler(settings=scheme))
    chart.plot(Volume(sma=2))
    (line,) = chart.canvas.main_axes().lines
    assert mcolors.to_rgba(line.get_color()) == rgba("purple")
    plt.close(chart.figure)


def test_shipped_style_colors_volume():
    fig, poly = plot_volume(style="nightclouds")
    assert rgb(poly.get_facecolor()) == [rgba("white")[:3], rgba("#4a90d9")[:3]]
    plt.close(fig)
