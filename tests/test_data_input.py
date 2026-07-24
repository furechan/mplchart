"""Tests for passing already-computed series data to renderer primitives."""

import numpy as np
import pytest
import matplotlib.pyplot as plt

from mplchart.chart import Chart
from mplchart.primitives import AreaPlot, BarPlot, LinePlot
from mplchart.samples import sample_prices

pd = pytest.importorskip("pandas")


@pytest.fixture
def prices():
    return sample_prices().tail(60)


def close_figure(chart):
    plt.close(chart.figure)


def test_lineplot_accepts_series(prices):
    sma = prices["close"].rolling(5).mean().rename("sma-5")
    chart = Chart(prices, figsize=(4, 3))
    chart.plot(LinePlot(sma))
    (line,) = chart.canvas.main_axes().lines
    assert line.get_label() == "sma-5"  # label from the series name
    assert len(line.get_xdata()) == len(prices)
    close_figure(chart)


def test_partial_series_aligns_by_date(prices):
    partial = prices["close"].tail(20).rename("tail")
    chart = Chart(prices, figsize=(4, 3))
    chart.plot(LinePlot(partial))
    (line,) = chart.canvas.main_axes().lines
    ydata = np.asarray(line.get_ydata(), dtype=float)
    assert len(ydata) == len(prices)  # reindexed to the full prices index
    assert np.isnan(ydata[: len(prices) - 20]).all()  # missing rows are NaN
    close_figure(chart)


def test_positional_data_must_be_full_length(prices):
    chart = Chart(prices, figsize=(4, 3))
    with pytest.raises(ValueError, match="full-length"):
        chart.plot(LinePlot(np.arange(5)))
    close_figure(chart)


def test_chart_plot_series_directly(prices):
    ema = prices["close"].ewm(span=10).mean().rename("ema-10")
    chart = Chart(prices, figsize=(4, 3))
    chart.plot(ema)  # dispatches through AutoPlot
    (line,) = chart.canvas.main_axes().lines
    assert line.get_label() == "ema-10"
    close_figure(chart)


def test_bar_and_area_accept_data(prices):
    delta = prices["close"].diff().rename("delta")
    chart = Chart(prices, figsize=(4, 3))
    chart.pane("below").plot(BarPlot(delta))
    chart.pane("below").plot(AreaPlot(delta))
    close_figure(chart)


def test_data_repr_is_truncated(prices):
    plot = LinePlot(prices["close"])
    assert "Series" in repr(plot)
    assert "\n" not in repr(plot)  # no data dump


def test_polars_series_positional():
    pl = pytest.importorskip("polars")

    prices = sample_prices(backend="polars").tail(60)
    chart = Chart(prices, figsize=(4, 3))
    chart.plot(LinePlot(prices["close"]))
    (line,) = chart.canvas.main_axes().lines
    assert line.get_label() == "close"
    close_figure(chart)

    chart = Chart(prices, figsize=(4, 3))
    with pytest.raises(ValueError, match="full-length"):
        chart.plot(LinePlot(pl.Series("x", [1.0, 2.0])))
    close_figure(chart)
