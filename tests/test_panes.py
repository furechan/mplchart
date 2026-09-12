"""Pane model tests — Pane is creative + sticky, renderer pane= is selective + ephemeral."""

import pytest
import matplotlib.pyplot as plt

from mplchart.chart import Chart
from mplchart.samples import sample_prices
from mplchart.primitives import Candlesticks, Pane, LinePlot, AreaPlot, BarPlot, Volume


@pytest.fixture(params=["pandas", "polars"])
def backend(request):
    pytest.importorskip(request.param)
    return request.param


@pytest.fixture
def prices(backend):
    return sample_prices(freq="daily", backend=backend).tail(100)


def test_pane_is_sticky(prices):
    # creation moves the current pane: followers land on the new pane
    chart = Chart(prices, figsize=(6, 4))
    chart.plot([Candlesticks(), Pane("below"), LinePlot("close"), LinePlot("open")])

    panes = chart.canvas.panes()
    assert len(panes) == 2
    assert len(panes[0].lines) == 0  # main: candles only
    assert len(panes[1].lines) == 2  # both lines followed the Pane
    plt.close(chart.figure)


def test_pane_above(prices):
    chart = Chart(prices, figsize=(6, 4))
    chart.plot([Candlesticks(), Pane("above"), LinePlot("close")])

    panes = chart.canvas.panes()
    assert len(panes) == 2
    assert chart.canvas.get_axes("same") is panes[-1]  # last created is current
    assert chart.canvas.get_axes("main") is panes[0]
    plt.close(chart.figure)


def test_pane_selecting_rejected(prices):
    # Pane is creational only — selection is not a Pane job
    chart = Chart(prices, figsize=(6, 4))
    with pytest.raises(ValueError, match="Invalid position"):
        chart.plot([Candlesticks(), Pane("main")])  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]
    plt.close(chart.figure)

    chart = Chart(prices, figsize=(6, 4))
    with pytest.raises(ValueError, match="Invalid position"):
        chart.pane("main")  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]
    plt.close(chart.figure)


def test_renderer_pane_is_ephemeral(prices):
    # the regression the model exists for: a punctual overlay on main does
    # not move the current pane — followers stay where they were
    chart = Chart(prices, figsize=(6, 4))
    chart.plot([
        Candlesticks(),
        Pane("below"),
        LinePlot("close"),
        LinePlot("open", pane="main"),  # one-off overlay on main
        LinePlot("high"),               # still lands in the lower pane
    ])

    panes = chart.canvas.panes()
    assert len(panes) == 2
    assert len(panes[0].lines) == 1  # the overlay
    assert len(panes[1].lines) == 2  # close + high
    plt.close(chart.figure)


def test_renderer_pane_creating_rejected(prices):
    chart = Chart(prices, figsize=(6, 4))
    with pytest.raises(ValueError, match="Invalid target"):
        chart.plot(LinePlot("close", pane="above"))  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]
    plt.close(chart.figure)


@pytest.mark.parametrize("renderer", [LinePlot, AreaPlot, BarPlot], ids=lambda r: r.__name__)
def test_renderers_accept_pane(prices, renderer):
    chart = Chart(prices, figsize=(6, 4))
    chart.plot([Candlesticks(), Pane("below"), renderer("close", pane="main")])

    panes = chart.canvas.panes()
    assert len(panes) == 2
    main_artists = len(panes[0].lines) + len(panes[0].collections) + len(panes[0].patches)
    lower_artists = len(panes[1].lines) + len(panes[1].collections) + len(panes[1].patches)
    assert main_artists > 2  # candles + the punctually placed renderer
    assert lower_artists == 0  # the new pane stayed empty
    plt.close(chart.figure)


@pytest.mark.parametrize("yaxis_log", [False, True])
def test_chart_yaxis_log(prices, yaxis_log):
    chart = Chart(prices, figsize=(6, 4), yaxis_log=yaxis_log)
    try:
        chart.plot(Candlesticks())
        main = chart.canvas.main_axes()
        _, lows = chart.view.series_xy(chart.view.eval("low"))
        _, highs = chart.view.series_xy(chart.view.eval("high"))
        low, high = min(lows), max(highs)
        assert main.dataLim.ymin == pytest.approx(low)
        assert main.dataLim.ymax == pytest.approx(high)
        lower, upper = main.get_ylim()
        assert 0 < lower < low < high < upper
        chart.plot(LinePlot("close"), Volume(), Pane("below"), LinePlot("close"))
        assert main.get_ylim() == pytest.approx((lower, upper))
        assert main.get_yscale() == ("log" if yaxis_log else "linear")
        for ax in chart.figure.axes:
            if ax is not main:
                assert ax.get_yscale() == "linear"
        assert b"<svg" in chart.render()
    finally:
        plt.close(chart.figure)


def test_volume_standalone(prices):
    # volume-only chart: the twinx request selects the empty main pane and
    # Volume owns it — full height, visible scale
    chart = Chart(prices, figsize=(6, 4))
    chart.plot(Volume(sma=50))

    assert chart.canvas.count_axes() == 1
    assert chart.canvas.count_axes(include_twins=True) == 1
    ax = chart.canvas.main_axes()
    assert ax.yaxis.get_visible()
    plt.close(chart.figure)


def test_volume_own_pane(prices):
    # the classic layout: a dedicated volume sub-pane — Volume owns the
    # fresh pane instead of twinning it
    chart = Chart(prices, figsize=(6, 4))
    chart.plot([Candlesticks(), Pane("below"), Volume()])

    assert chart.canvas.count_axes() == 2
    assert chart.canvas.count_axes(include_twins=True) == 2  # no twin
    lower = chart.canvas.panes()[-1]
    assert lower.yaxis.get_visible()
    plt.close(chart.figure)


def test_volume_overlay(prices):
    # with a pane present, Volume rides a twinx overlay: squashed, scale hidden
    chart = Chart(prices, figsize=(6, 4))
    chart.plot([Candlesticks(), Volume()])

    assert chart.canvas.count_axes() == 1
    assert chart.canvas.count_axes(include_twins=True) == 2
    twin = next(ax for ax in chart.figure.axes if getattr(ax, "_label", None) == "twinx")
    assert not twin.yaxis.get_visible()
    plt.close(chart.figure)


@pytest.mark.parametrize("position", ["above", "below"])
def test_pane_before_plot_preserves_empty_main(prices, position):
    chart = Chart(prices, figsize=(6, 4))
    main = chart.canvas.main_axes()
    chart.pane(position).plot(LinePlot("close"))
    assert len(chart.canvas.panes()) == 2
    assert not main.has_data()
    assert len(chart.canvas.get_axes().lines) == 1
    assert chart.canvas.main_axes() is main
    plt.close(chart.figure)
