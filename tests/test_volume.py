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


def test_use_prev_close_kwarg():
    # interbar: bar 1 closes above the previous close, so both bars are up
    # (the first bar compares to itself)
    fig, poly = plot_volume(colorup="green", colordn="red", use_prev_close=True)
    assert rgb(poly.get_facecolor()) == [rgba("green")[:3]] * 2
    plt.close(fig)


def test_use_prev_close_setting():
    # a style can declare the interbar mode; the kwarg wins over the setting
    scheme = {"volume.up.color": "green", "volume.down.color": "red",
              "volume.use_prev_close": True}
    fig, poly = plot_volume(settings=scheme)
    assert rgb(poly.get_facecolor()) == [rgba("green")[:3]] * 2
    plt.close(fig)

    fig, poly = plot_volume(settings=scheme, use_prev_close=False)
    assert rgb(poly.get_facecolor()) == [rgba("green")[:3], rgba("red")[:3]]
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


def test_edge_colors_default_none():
    # bars are unoutlined by default
    fig, poly = plot_volume()
    assert len(poly.get_edgecolor()) == 0 or all(c[3] == 0 for c in poly.get_edgecolor())
    plt.close(fig)


def test_edge_colors_kwargs():
    # directional outlines, mirroring the face colors
    fig, poly = plot_volume(edgeup="navy", edgedn="purple")
    assert rgb(poly.get_edgecolor()) == [rgba("navy")[:3], rgba("purple")[:3]]
    plt.close(fig)


def test_edge_colors_setting_neutral():
    # both sides alike gives a neutral outline (the tradingview look)
    scheme = {"volume.edge.up.color": "white", "volume.edge.down.color": "white"}
    fig, poly = plot_volume(settings=scheme)
    assert rgb(poly.get_edgecolor()) == [rgba("white")[:3]] * 2
    plt.close(fig)


def test_edge_one_side_only():
    # with one side set the other follows its face color (candle-edge rule),
    # so the down bar's outline matches its fill rather than going black
    fig, poly = plot_volume(colorup="green", colordn="red", edgeup="navy")
    assert rgb(poly.get_edgecolor()) == [rgba("navy")[:3], rgba("red")[:3]]
    plt.close(fig)


def test_edge_lightness_opts_in():
    # lightness alone opts the outlines in: edges default to the faces,
    # then the transform scales their lightness (the mpf implicit rim)
    from mplchart.colors import scale_lightness

    scheme = {"volume.edge.lightness": 0.9}
    fig, poly = plot_volume(settings=scheme, colorup="#4dc790", colordn="#fd6b6c")
    expected = [rgba(scale_lightness(c, 0.9))[:3] for c in ("#4dc790", "#fd6b6c")]
    assert rgb(poly.get_edgecolor()) == expected
    plt.close(fig)


def test_edge_lightness_transforms_explicit_colors():
    # lightness is a final transform — it adjusts an explicit edge color too
    from mplchart.colors import scale_lightness

    scheme = {"volume.edge.lightness": 1.2}
    fig, poly = plot_volume(settings=scheme, colorup="green", colordn="red", edgeup="navy")
    expected = [rgba(scale_lightness("navy", 1.2))[:3], rgba(scale_lightness("red", 1.2))[:3]]
    assert rgb(poly.get_edgecolor()) == expected
    plt.close(fig)
