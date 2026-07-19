"""Series primitives: string-column form and single-series contract."""

import pytest
import matplotlib.pyplot as plt

from mplchart.chart import Chart
from mplchart.samples import sample_prices
from mplchart.primitives import LinePlot, BarPlot, AreaPlot

BACKENDS = ["pandas", "polars"]


@pytest.mark.parametrize("backend", BACKENDS)
def test_string_indicator_plots_price_column(backend):
    pytest.importorskip(backend)
    prices = sample_prices(freq="daily", backend=backend)
    chart = Chart(prices, max_bars=100)
    chart.plot(LinePlot("close"), BarPlot("volume"), AreaPlot("open"))
    assert chart.count_axes() > 0
    plt.close()


def test_string_indicator_stays_a_string():
    lp = LinePlot("close")
    assert lp.indicator == "close"


@pytest.mark.parametrize("backend", BACKENDS)
def test_plot_string_directly(backend):
    """A bare column name is a first-class plot item (implicit AutoPlot)."""
    pytest.importorskip(backend)
    prices = sample_prices(freq="daily", backend=backend)
    chart = Chart(prices, max_bars=100)
    chart.plot("close")
    assert chart.count_axes() > 0
    plt.close()


def test_unknown_column_raises():
    pytest.importorskip("polars")
    prices = sample_prices(freq="daily", backend="polars")
    chart = Chart(prices, max_bars=100)
    with pytest.raises(Exception, match="nope"):
        chart.plot(LinePlot("nope"))
    plt.close()


def test_bare_series_primitive_requires_indicator():
    pytest.importorskip("polars")
    prices = sample_prices(freq="daily", backend="polars")
    chart = Chart(prices, max_bars=100)
    with pytest.raises(ValueError, match="requires an indicator"):
        chart.plot(LinePlot())
    plt.close()


def test_multi_output_requires_composition():
    pytest.importorskip("polars")
    from mplchart.expressions import MACD

    prices = sample_prices(freq="daily", backend="polars")
    chart = Chart(prices, max_bars=100)
    with pytest.raises(ValueError, match="single-output expression"):
        chart.plot(LinePlot(MACD()))
    plt.close()


def test_struct_field_selects_one_output():
    pytest.importorskip("polars")
    from mplchart.expressions import MACD

    prices = sample_prices(freq="daily", backend="polars")
    chart = Chart(prices, max_bars=100)
    chart.plot(LinePlot(MACD().struct.field("macdhist")))
    assert chart.count_axes() > 0
    plt.close()
