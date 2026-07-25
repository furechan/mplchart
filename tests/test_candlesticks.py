"""Tests for the Candlesticks color-scheme kwargs (atomic schemes → six colors)."""

import pytest
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from mplchart.chart import Chart
from mplchart.primitives import Candlesticks
from mplchart.styles import Styler

pd = pytest.importorskip("pandas")


def make_prices():
    """Three bars: up, down, doji (counts as up)."""
    return pd.DataFrame(
        {
            "open": [10.0, 11.0, 10.0],
            "high": [11.5, 11.5, 10.5],
            "low": [9.5, 9.5, 9.5],
            "close": [11.0, 10.0, 10.0],
            "volume": [100, 100, 100],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="D"),
    )


def plot_candles(settings=(), style=None, **kwargs):
    """Plot and return (wicks, poly) collections; caller closes the figure."""
    chart = Chart(make_prices(), figsize=(4, 3), style=style or Styler(settings=settings))
    chart.plot(Candlesticks(**kwargs))
    ax = chart.canvas.main_axes()
    wicks, poly = ax.collections
    return chart.figure, wicks, poly


def rgba(color):
    return mcolors.to_rgba(color)


def test_default_mono_hollow():
    fig, wicks, poly = plot_candles()
    textcolor = rgba(plt.rcParams["text.color"])
    background = rgba(plt.rcParams["axes.facecolor"])
    faces = [tuple(c) for c in poly.get_facecolor()]
    edges = [tuple(c) for c in poly.get_edgecolor()]
    assert faces == [background, textcolor, background]  # up hollow, dn filled
    assert edges == [textcolor] * 3
    plt.close(fig)


def test_mono_color_kwarg():
    fig, wicks, poly = plot_candles(color="navy")
    navy, white = rgba("navy"), rgba(plt.rcParams["axes.facecolor"])
    assert [tuple(c) for c in poly.get_facecolor()] == [white, navy, white]
    assert [tuple(c) for c in poly.get_edgecolor()] == [navy] * 3
    assert {tuple(c) for c in wicks.get_color()} == {navy}
    plt.close(fig)


def test_bicolor_filled():
    fig, wicks, poly = plot_candles(colorup="green", colordn="red")
    green, red = rgba("green"), rgba("red")
    assert [tuple(c) for c in poly.get_facecolor()] == [green, red, green]
    assert [tuple(c) for c in poly.get_edgecolor()] == [green, red, green]
    # wick segments interleave per bar: (upper, lower) × 3 bars
    assert [tuple(c) for c in wicks.get_color()] == [green] * 2 + [red] * 2 + [green] * 2
    plt.close(fig)


def test_bicolor_hollow():
    fig, wicks, poly = plot_candles(colorup="green", colordn="red", hollow=True)
    green, red = rgba("green"), rgba("red")
    background = rgba(plt.rcParams["axes.facecolor"])
    assert [tuple(c) for c in poly.get_facecolor()] == [background, red, background]
    assert [tuple(c) for c in poly.get_edgecolor()] == [green, red, green]
    assert [tuple(c) for c in wicks.get_color()] == [green] * 2 + [red] * 2 + [green] * 2
    plt.close(fig)


def test_mono_hollow_explicit():
    # hollow=True resolves to the mono family default — same as no kwargs
    fig, wicks, poly = plot_candles(hollow=True)
    background = rgba(plt.rcParams["axes.facecolor"])
    textcolor = rgba(plt.rcParams["text.color"])
    assert [tuple(c) for c in poly.get_facecolor()] == [background, textcolor, background]
    plt.close(fig)


def test_settings_bicolor_filled():
    # candle.up/down settings select the filled bicolor family
    scheme = {"candle.up.color": "green", "candle.down.color": "red"}
    fig, wicks, poly = plot_candles(settings=scheme)
    green, red = rgba("green"), rgba("red")
    assert [tuple(c) for c in poly.get_facecolor()] == [green, red, green]
    assert [tuple(c) for c in poly.get_edgecolor()] == [green, red, green]
    plt.close(fig)


def test_settings_bicolor_hollow_kwarg():
    # the hollow kwarg overrides the settings family's filled default
    scheme = {"candle.up.color": "green", "candle.down.color": "red"}
    fig, wicks, poly = plot_candles(settings=scheme, hollow=True)
    green, red = rgba("green"), rgba("red")
    background = rgba(plt.rcParams["axes.facecolor"])
    assert [tuple(c) for c in poly.get_facecolor()] == [background, red, background]
    assert [tuple(c) for c in poly.get_edgecolor()] == [green, red, green]
    plt.close(fig)


def test_settings_neutral_wick():
    # wicks gives yahoo-style neutral wicks; edges keep the up/down colors
    scheme = {"candle.up.color": "green", "candle.down.color": "red", "wicks.color": "gray"}
    fig, wicks, poly = plot_candles(settings=scheme)
    green, red, gray = rgba("green"), rgba("red"), rgba("gray")
    assert [tuple(c) for c in poly.get_edgecolor()] == [green, red, green]
    assert {tuple(c) for c in wicks.get_color()} == {gray}
    plt.close(fig)


def test_settings_edge_colors():
    # edge.up/edge.down override the body outlines; wicks follow the edges
    scheme = {
        "candle.up.color": "green", "candle.down.color": "red",
        "edge.up.color": "navy", "edge.down.color": "purple",
    }
    fig, wicks, poly = plot_candles(settings=scheme)
    green, red = rgba("green"), rgba("red")
    navy, purple = rgba("navy"), rgba("purple")
    assert [tuple(c) for c in poly.get_facecolor()] == [green, red, green]
    assert [tuple(c) for c in poly.get_edgecolor()] == [navy, purple, navy]
    assert [tuple(c) for c in wicks.get_color()] == [navy] * 2 + [purple] * 2 + [navy] * 2
    plt.close(fig)


def test_settings_hollow_color():
    # candle.off sets the hollow-body fill without flipping the family
    scheme = {"candle.off.color": "lightyellow"}
    fig, wicks, poly = plot_candles(settings=scheme)
    fill = rgba("lightyellow")
    textcolor = rgba(plt.rcParams["text.color"])
    assert [tuple(c) for c in poly.get_facecolor()] == [fill, textcolor, fill]
    assert [tuple(c) for c in poly.get_edgecolor()] == [textcolor] * 3
    plt.close(fig)


def test_settings_candle_alpha():
    # candle.alpha is a non-color facet — canonical dotted key
    style = Styler(settings={"candle.alpha": 0.25})
    fig, wicks, poly = plot_candles(style=style)
    assert poly.get_alpha() == 0.25
    assert wicks.get_alpha() == 0.25
    plt.close(fig)

    # explicit kwarg wins over the setting
    fig, wicks, poly = plot_candles(style=style, alpha=0.75)
    assert poly.get_alpha() == 0.75
    plt.close(fig)


def test_settings_mode_flags():
    # candle.hollow / candle.use_prev_close — style-side mode flags (kwarg mirrors)
    style = Styler(settings={
        "candle.up.color": "green", "candle.down.color": "red",
        "candle.hollow": True, "candle.use_prev_close": True,
    })
    fig, wicks, poly = plot_candles(style=style)  # StockCharts, fully style-side
    green, red = rgba("green"), rgba("red")
    background = rgba(plt.rcParams["axes.facecolor"])
    assert [tuple(c) for c in poly.get_facecolor()] == [background, red, background]
    assert [tuple(c) for c in poly.get_edgecolor()] == [green, red, green]
    plt.close(fig)

    # explicit kwargs beat the settings
    fig, wicks, poly = plot_candles(style=style, hollow=False, use_prev_close=False)
    assert [tuple(c) for c in poly.get_facecolor()] == [green, red, green]
    plt.close(fig)


def test_settings_use_prev_close_interbar():
    # the setting genuinely switches the criterion (gap-up bar: intrabar dn, interbar up)
    prices = pd.DataFrame(
        {
            "open": [10.0, 12.0],
            "high": [12.0, 12.5],
            "low": [9.5, 11.0],
            "close": [10.0, 11.5],
            "volume": [100, 100],
        },
        index=pd.date_range("2024-01-01", periods=2, freq="D"),
    )
    style = Styler(settings={
        "candle.up.color": "green", "candle.down.color": "red",
        "candle.use_prev_close": True,
    })
    chart = Chart(prices, figsize=(4, 3), style=style)
    chart.plot(Candlesticks())
    wicks, poly = chart.canvas.main_axes().collections
    assert tuple(poly.get_facecolor()[1]) == rgba("green")  # interbar up
    plt.close(chart.figure)


def test_kwarg_scheme_is_atomic():
    # a kwarg scheme never merges with settings — missing side falls to textcolor
    scheme = {"candle.down.color": "blue"}
    fig, wicks, poly = plot_candles(settings=scheme, colorup="green")
    green = rgba("green")
    textcolor = rgba(plt.rcParams["text.color"])
    assert [tuple(c) for c in poly.get_facecolor()] == [green, textcolor, green]
    plt.close(fig)


def test_use_prev_close_interbar_coloring():
    # bar 1 gaps up but closes below its open: intrabar → dn, interbar → up
    prices = pd.DataFrame(
        {
            "open": [10.0, 12.0],
            "high": [12.0, 12.5],
            "low": [9.5, 11.0],
            "close": [10.0, 11.5],
            "volume": [100, 100],
        },
        index=pd.date_range("2024-01-01", periods=2, freq="D"),
    )
    green, red = rgba("green"), rgba("red")

    for use_prev_close, expected in [(False, red), (True, green)]:
        chart = Chart(prices, figsize=(4, 3))
        chart.plot(Candlesticks(colorup="green", colordn="red", use_prev_close=use_prev_close))
        wicks, poly = chart.canvas.main_axes().collections
        assert tuple(poly.get_facecolor()[1]) == expected
        plt.close(chart.figure)


def test_tuple_color_kwargs():
    # RGB tuples normalize to hex before np.where — no broadcast breakage
    rgb = (0.2, 0.65, 0.6)
    fig, wicks, poly = plot_candles(colorup=rgb, colordn="red")
    assert tuple(poly.get_facecolor()[0]) == rgba(mcolors.to_hex(rgb))  # hex-quantized
    plt.close(fig)


def test_dual_criteria_stockcharts_cell():
    """Hollow × interbar: fill stays intrabar while color follows prev-close."""
    import numpy as np
    from mplchart.primitives.candlesticks import plot_cspoly

    open_ = np.array([10.0, 12.0, 10.0])
    high = np.array([12.0, 12.5, 10.5])
    low = np.array([9.5, 11.0, 9.5])
    close = np.array([10.0, 11.5, 10.2])  # body: up, dn, up — trend: up, up, dn
    green, red, white = rgba("green"), rgba("red"), rgba("white")

    fig, ax = plt.subplots()
    plot_cspoly(
        np.arange(3), open_, high, low, close, ax=ax, width=0.8, alpha=1.0,
        faceup="green", facedn="red", edgeup="green", edgedn="red",
        wickup="green", wickdn="red", faceoff="white", use_prev_close=True,
    )
    wicks, poly = ax.collections
    faces = np.asarray(poly.get_facecolor())
    edges = np.asarray(poly.get_edgecolor())
    assert [tuple(c) for c in faces] == [white, green, white]  # hollow by intrabar
    assert [tuple(c) for c in edges] == [green, green, red]  # color by interbar
    plt.close(fig)


def test_settings_stockcharts_cell():
    # settings palette + mode kwargs: the StockCharts look needs no color kwargs
    scheme = {"candle.up.color": "green", "candle.down.color": "red"}
    fig, wicks, poly = plot_candles(settings=scheme, hollow=True, use_prev_close=True)
    red = rgba("red")
    background = rgba(plt.rcParams["axes.facecolor"])
    assert [tuple(c) for c in poly.get_facecolor()] == [background, red, background]
    plt.close(fig)


def test_mono_kwarg_use_prev_close_rejected():
    # params-only consistency: explicit mono color vs the interbar criterion
    with pytest.raises(ValueError, match="use_prev_close requires"):
        plot_candles(color="navy", use_prev_close=True)
    plt.close("all")


def test_competing_schemes_rejected():
    with pytest.raises(ValueError, match="color together with"):
        Candlesticks(color="navy", colorup="green")


def test_mono_kwarg_filled_rejected():
    # params-only consistency: explicit mono color vs hollow=False
    with pytest.raises(ValueError, match="need hollow"):
        plot_candles(color="navy", hollow=False)
    plt.close("all")


def test_default_mode_flags_render():
    # default mode is never validated against settings — flags apply as-is
    fig, wicks, poly = plot_candles(hollow=False)  # mono filled, direction-blind
    textcolor = rgba(plt.rcParams["text.color"])
    assert [tuple(c) for c in poly.get_facecolor()] == [textcolor] * 3
    plt.close(fig)

    fig, wicks, poly = plot_candles(use_prev_close=True)  # renders, colors moot
    plt.close(fig)


def test_label_kwarg():
    chart = Chart(make_prices(), figsize=(4, 3))
    chart.plot(Candlesticks(label="Candles"))
    wicks, poly = chart.canvas.main_axes().collections
    assert poly.get_label() == "Candles"
    plt.close(chart.figure)


def double_ohlc(prices):
    return prices[["open", "high", "low", "close"]] * 2


def test_indicator_binding():
    # positional indicator supplies alternative OHLC data
    chart = Chart(make_prices(), figsize=(4, 3))
    chart.plot(Candlesticks(double_ohlc))
    wicks, poly = chart.canvas.main_axes().collections
    ys = poly.get_paths()[0].vertices[:, 1]
    assert ys.max() == 22.0  # first bar body top = close * 2
    plt.close(chart.figure)


def test_indicator_matmul_binding():
    prim = double_ohlc @ Candlesticks()
    assert prim.indicator is double_ohlc


def test_indicator_requires_ohlc():
    chart = Chart(make_prices(), figsize=(4, 3))
    with pytest.raises(ValueError, match="OHLC columns"):
        chart.plot(Candlesticks(lambda prices: prices["close"]))
    plt.close("all")


def test_color_scheme_deprecated():
    # color_scheme is deprecated and ignored — warn at Chart, default look renders
    with pytest.warns(DeprecationWarning, match="color_scheme is deprecated"):
        chart = Chart(make_prices(), figsize=(4, 3), color_scheme={"candle.up": "green"})
    chart.plot(Candlesticks())
    wicks, poly = chart.canvas.main_axes().collections
    textcolor = rgba(plt.rcParams["text.color"])
    assert tuple(poly.get_facecolor()[1]) == textcolor  # scheme ignored
    plt.close(chart.figure)
