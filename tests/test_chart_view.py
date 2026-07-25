"""Chart.get_view tests — lazy creation, caching, transform — both backends."""

import pytest
import matplotlib.pyplot as plt

from mplchart.chart import Chart
from mplchart.samples import sample_prices
from mplchart.primitives import Candlesticks


@pytest.fixture(params=["pandas", "polars"])
def backend(request):
    pytest.importorskip(request.param)
    return request.param


@pytest.fixture
def prices(backend):
    return sample_prices(freq="daily", backend=backend).tail(100)


def head_transform(prices):
    """stand-in domain transform — keeps the frame shape, halves the rows"""
    return prices.head(50)


def test_view_lazy_and_cached(prices):
    chart = Chart(prices, figsize=(4, 3))
    assert chart._view is None  # not created at init
    view = chart.view
    assert view is chart.view
    assert view is chart.get_view()
    plt.close(chart.figure)


def test_transform_applied(prices):
    chart = Chart(prices, figsize=(4, 3))
    view = chart.get_view(transform=head_transform)
    assert len(view.prices) == 50
    assert view is chart.view  # cached — later accesses see the transformed view
    plt.close(chart.figure)


def test_transform_after_creation_raises(prices):
    chart = Chart(prices, figsize=(4, 3))
    chart.view  # first access creates the view
    with pytest.raises(ValueError, match="already created"):
        chart.get_view(transform=head_transform)
    plt.close(chart.figure)


def test_transform_with_raw_dates_raises(prices):
    chart = Chart(prices, figsize=(4, 3), raw_dates=True)
    with pytest.raises(ValueError, match="raw_dates"):
        chart.get_view(transform=head_transform)
    plt.close(chart.figure)


def test_plot_over_transformed_view(prices):
    # the primitive-first flow: bind the transform, then plot as usual
    chart = Chart(prices, figsize=(4, 3))
    chart.get_view(transform=head_transform)
    chart.plot(Candlesticks())
    assert chart.canvas.count_axes() > 0
    plt.close(chart.figure)


def test_init_prices_again_warns(prices):
    chart = Chart(prices, figsize=(4, 3))
    with pytest.warns(UserWarning, match="already called"):
        chart.init_prices(prices)
    plt.close(chart.figure)
