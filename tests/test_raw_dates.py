"""Tests for the backend-native data views and raw_dates mode."""

import pytest
import numpy as np
import matplotlib.pyplot as plt

from mplchart.dataview import get_view, PandasDataView, PolarsDataView


BACKENDS = ["pandas", "polars"]
MODES = [False, True]

PUBLIC_METHODS = ("slice", "series_xy", "map_date", "eval")
PUBLIC_ATTRS = ("prices", "dates", "xloc", "raw_dates", "start", "end", "max_bars")


def make_prices(backend, n=50, start="2024-01-01"):
    """Synthetic daily prices frame for the given backend."""
    dates = (np.datetime64(start) + np.arange(n)).astype("datetime64[us]")
    close = np.arange(n, dtype=float)
    if backend == "polars":
        pl = pytest.importorskip("polars")
        return pl.DataFrame({"date": dates, "close": close})
    pd = pytest.importorskip("pandas")
    return pd.DataFrame({"close": close}, index=pd.DatetimeIndex(dates, name="date"))


def make_view(backend, raw_dates=False, n=50, **window):
    return get_view(make_prices(backend, n=n), raw_dates=raw_dates, **window)


# --- factory routing and public interface ---

def test_get_view_routes_by_backend():
    pytest.importorskip("pandas")
    pytest.importorskip("polars")
    assert isinstance(get_view(make_prices("pandas")), PandasDataView)
    assert isinstance(get_view(make_prices("polars")), PolarsDataView)


def test_get_view_rejects_unsupported():
    with pytest.raises(ValueError, match="backend"):
        get_view({"close": [1, 2, 3]})


def test_chart_mapper_deprecated_alias():
    pytest.importorskip("pandas")
    from mplchart.chart import Chart
    from mplchart.samples import sample_prices

    chart = Chart(sample_prices(freq="daily", backend="pandas"), max_bars=50)
    with pytest.warns(DeprecationWarning, match="chart.view"):
        assert chart.mapper is chart.view
    plt.close()


@pytest.mark.parametrize("backend", BACKENDS)
def test_view_public_interface(backend):
    view = make_view(backend, max_bars=20)
    for name in PUBLIC_METHODS:
        assert callable(getattr(view, name)), f"missing method {name!r}"
    for name in PUBLIC_ATTRS:
        assert hasattr(view, name), f"missing attribute {name!r}"


# --- window resolution (via public outputs) ---

@pytest.mark.parametrize("backend", BACKENDS)
def test_window_max_bars(backend):
    view = make_view(backend, n=100, max_bars=20)
    xs, ys = view.series_xy(np.arange(100))
    assert len(xs) == len(ys) == 20
    np.testing.assert_array_equal(ys, np.arange(80, 100))


@pytest.mark.parametrize("backend", BACKENDS)
def test_window_start_end_inclusive(backend):
    dates = (np.datetime64("2024-01-01") + np.arange(100)).astype("datetime64[us]")
    view = make_view(backend, n=100, start=dates[10].item(), end=dates[30].item())
    xs, ys = view.series_xy(np.arange(100))
    assert len(xs) == 21  # end is inclusive (side="right")
    assert ys[0] == 10
    assert ys[-1] == 30


def test_backends_agree_on_window():
    pytest.importorskip("pandas")
    pytest.importorskip("polars")
    window = dict(start="2024-01-06", end="2024-03-01", max_bars=30)
    xs_pd, ys_pd = make_view("pandas", n=100, **window).series_xy(np.arange(100))
    xs_pl, ys_pl = make_view("polars", n=100, **window).series_xy(np.arange(100))
    np.testing.assert_array_equal(xs_pd, xs_pl)
    np.testing.assert_array_equal(ys_pd, ys_pl)


# --- x-coordinate semantics per mode ---

@pytest.mark.parametrize("backend", BACKENDS)
def test_series_xy_rownum_mode_integer_xs(backend):
    xs, ys = make_view(backend, max_bars=10).series_xy(np.arange(50))
    assert xs.dtype.kind == "i"
    assert len(xs) == len(ys) == 10


@pytest.mark.parametrize("backend", BACKENDS)
def test_series_xy_raw_mode_datetime_xs(backend):
    xs, ys = make_view(backend, raw_dates=True, max_bars=10).series_xy(np.arange(50))
    assert xs.dtype.kind == "M"
    assert len(xs) == len(ys) == 10


@pytest.mark.parametrize("raw_dates", MODES)
@pytest.mark.parametrize("backend", BACKENDS)
def test_series_xy_variadic(backend, raw_dates):
    """Multiple value arrays are cut by the same window in one call."""
    view = make_view(backend, raw_dates=raw_dates, max_bars=10)
    y1 = np.arange(50, dtype=float)
    y2 = np.arange(50, 100, dtype=float)
    xs, s1, s2 = view.series_xy(y1, y2)
    assert len(xs) == len(s1) == len(s2) == 10
    np.testing.assert_array_equal(s1, y1[-10:])
    np.testing.assert_array_equal(s2, y2[-10:])


@pytest.mark.parametrize("backend", BACKENDS)
def test_series_xy_accepts_native_series(backend):
    """Native Series inputs are windowed positionally, same as arrays."""
    prices = make_prices(backend)
    view = get_view(prices, max_bars=10)
    xs, ys = view.series_xy(prices["close"])
    np.testing.assert_array_equal(ys, np.arange(40, 50, dtype=float))


@pytest.mark.parametrize("backend", BACKENDS)
def test_map_date_rownum_mode_returns_int(backend):
    view = make_view(backend)
    out = view.map_date("2024-01-11")
    assert isinstance(out, int)
    assert out == 10


@pytest.mark.parametrize("backend", BACKENDS)
def test_map_date_raw_mode_returns_datetime(backend):
    view = make_view(backend, raw_dates=True)
    out = view.map_date("2024-01-11")
    assert isinstance(out, np.datetime64)
    assert out == np.datetime64("2024-01-11")


# --- eval ---

@pytest.mark.parametrize("backend", BACKENDS)
def test_eval_column_string(backend):
    prices = make_prices(backend)
    view = get_view(prices, max_bars=10)
    result = view.eval("close")
    assert len(result) == len(prices)  # full-length, no windowing
    np.testing.assert_array_equal(np.asarray(result), np.arange(50, dtype=float))


@pytest.mark.parametrize("backend", BACKENDS)
def test_eval_callable(backend):
    view = make_view(backend)
    result = view.eval(lambda prices: prices["close"])
    assert len(result) == 50


def test_eval_unrecognized_raises():
    view = make_view("pandas")
    with pytest.raises(TypeError, match="PandasDataView cannot evaluate"):
        view.eval(123)


def test_eval_backend_mismatch_raises():
    pl = pytest.importorskip("polars")
    view = make_view("pandas")
    with pytest.raises(TypeError, match="cannot evaluate"):
        view.eval(pl.col("close") * 2)


def test_apply_indicator_deprecated_alias():
    from mplchart.utils import apply_indicator

    prices = make_prices("pandas")
    with pytest.warns(DeprecationWarning, match="view.eval"):
        result = apply_indicator(prices, "close")
    assert len(result) == len(prices)


# --- slice ---

@pytest.mark.parametrize("raw_dates", MODES)
@pytest.mark.parametrize("backend", BACKENDS)
def test_slice_prices_with_xcol(backend, raw_dates):
    prices = make_prices(backend, n=50)
    view = get_view(prices, raw_dates=raw_dates, max_bars=10)
    sliced = view.slice(prices, xcol="xloc")
    assert len(sliced) == 10
    assert "xloc" in sliced.columns
    xloc = sliced["xloc"].to_numpy()
    if raw_dates:
        assert xloc.dtype.kind == "M"
    else:
        np.testing.assert_array_equal(xloc, np.arange(40, 50))


# --- Chart smoke tests with raw_dates=True ---

@pytest.mark.pandas
def test_chart_raw_dates_pandas():
    pytest.importorskip("pandas")
    from mplchart.chart import Chart
    from mplchart.samples import sample_prices
    from mplchart.primitives import Candlesticks, LinePlot
    from mplchart.indicators import SMA

    prices = sample_prices(freq="daily", backend="pandas")
    chart = Chart(prices, max_bars=100, raw_dates=True)
    assert chart.view is not None
    assert chart.view.raw_dates is True
    chart.plot(Candlesticks(), SMA(20) @ LinePlot())
    assert chart.canvas.count_axes() > 0
    plt.close()


@pytest.mark.polars
def test_chart_raw_dates_polars_autoplot():
    pytest.importorskip("polars")
    from mplchart.chart import Chart
    from mplchart.samples import sample_prices
    from mplchart.primitives import AutoPlot
    from mplchart.expressions import SMA

    prices = sample_prices(freq="daily", backend="polars")
    chart = Chart(prices, max_bars=100, raw_dates=True)
    assert chart.view is not None
    assert chart.view.raw_dates is True
    chart.plot(SMA(20))                                  # implicit AutoPlot
    chart.plot(SMA(50) @ AutoPlot(label="trend"))        # AutoPlot override
    assert chart.canvas.count_axes() > 0
    plt.close()


@pytest.mark.polars
def test_chart_raw_dates_polars_multi_output():
    pytest.importorskip("polars")
    from mplchart.chart import Chart
    from mplchart.samples import sample_prices
    from mplchart.expressions import MACD

    prices = sample_prices(freq="daily", backend="polars")
    chart = Chart(prices, max_bars=100, raw_dates=True)
    chart.plot(MACD())
    assert chart.canvas.count_axes() > 0
    plt.close()


def test_chart_default_mode_uses_rownum():
    pytest.importorskip("polars")
    from mplchart.chart import Chart
    from mplchart.samples import sample_prices

    prices = sample_prices(freq="daily", backend="polars")
    chart = Chart(prices, max_bars=100)
    assert chart.view is not None
    assert chart.view.raw_dates is False
    plt.close()


@pytest.mark.parametrize("backend", BACKENDS)
def test_series_xy_rejects_wrong_length(backend):
    """The full-length assumption is enforced, not silently clamped."""
    view = make_view(backend, n=50, max_bars=10)
    with pytest.raises(ValueError, match="full-length"):
        view.series_xy(np.arange(30))
