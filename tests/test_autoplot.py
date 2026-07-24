"""Tests for AutoPlot dispatch, the Bands primitive, and renderer styling keys."""

import pytest
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

pd = pytest.importorskip("pandas")
pytestmark = pytest.mark.pandas

from mplchart.chart import Chart  # noqa: E402
from mplchart.indicators import BBANDS, MACD, SMA  # noqa: E402
from mplchart.primitives import Bands, LinePlot  # noqa: E402
from mplchart.samples import sample_prices  # noqa: E402
from mplchart.styles import Styler  # noqa: E402


@pytest.fixture
def prices():
    return sample_prices().tail(60)


def rgb(color):
    return mcolors.to_rgba(color)[:3]


def test_macd_dispatch_and_settings(prices):
    style = Styler(settings={
        "macd.color": "navy", "macdsignal.color": "purple", "macdhist.color": "orange",
    })
    chart = Chart(prices, figsize=(4, 3), style=style)
    chart.pane("below").plot(MACD())
    ax = chart.canvas.get_axes("same")

    macd_line, signal_line = ax.lines
    assert mcolors.to_rgba(macd_line.get_color())[:3] == rgb("navy")
    assert mcolors.to_rgba(signal_line.get_color())[:3] == rgb("purple")
    assert signal_line.get_label().startswith("_")  # only the first column labeled

    (bars,) = ax.collections
    assert tuple(bars.get_facecolor()[0])[:3] == rgb("orange")
    plt.close(chart.figure)


def test_bbands_dispatches_to_bands(prices):
    style = Styler(settings={"bands.color": "teal"})
    chart = Chart(prices, figsize=(4, 3), style=style)
    chart.plot(BBANDS(20))
    ax = chart.canvas.main_axes()

    assert len(ax.lines) == 3  # middle dashed + lower/upper dotted
    assert {line.get_linestyle() for line in ax.lines} == {"--", ":"}
    assert all(mcolors.to_rgba(line.get_color())[:3] == rgb("teal") for line in ax.lines)
    (fill,) = ax.collections
    assert tuple(fill.get_facecolor()[0])[:3] == rgb("teal")
    plt.close(chart.figure)


def test_bands_custom_columns(prices):
    frame = pd.DataFrame({
        "hi": prices["close"] + 1.0,
        "lo": prices["close"] - 1.0,
    })
    chart = Chart(prices, figsize=(4, 3))
    chart.plot(Bands(frame, upper="hi", lower="lo"))
    ax = chart.canvas.main_axes()
    assert len(ax.lines) == 2  # no middle column
    assert len(ax.collections) == 1
    plt.close(chart.figure)


def test_bands_requires_band_columns(prices):
    chart = Chart(prices, figsize=(4, 3))
    with pytest.raises(ValueError, match="upperband"):
        chart.plot(Bands(SMA(20)))
    plt.close(chart.figure)


def test_lineplot_honors_settings(prices):
    # renderers resolve colors by name — the old AutoPlot-only asymmetry is gone
    style = Styler(settings={"sma.color": "crimson"})
    chart = Chart(prices, figsize=(4, 3), style=style)
    chart.plot(LinePlot(SMA(20)))
    (line,) = chart.canvas.main_axes().lines
    assert mcolors.to_rgba(line.get_color())[:3] == rgb("crimson")
    plt.close(chart.figure)
