"""Tests for raw_dates mode and RawDateMapper / DateIndexMapper interface parity."""

import pytest
import numpy as np
import matplotlib.pyplot as plt

from mplchart.mapper import DateIndexMapper, RawDateMapper


MAPPER_CLASSES = [DateIndexMapper, RawDateMapper]

PUBLIC_METHODS = (
    "series_xy", "slice",
    "slice_polars", "slice_pandas", "map_date", "config_axes",
)
PUBLIC_ATTRS = ("datetime_array", "rownum", "max_bars", "start", "end")


def _datetime_array(n=50, start="2024-01-01"):
    return (np.datetime64(start) + np.arange(n)).astype("datetime64[ns]")


# --- interface parity ---

@pytest.mark.parametrize("cls", MAPPER_CLASSES, ids=lambda c: c.__name__)
def test_mapper_has_public_methods(cls):
    mapper = cls(datetime_array=_datetime_array(), max_bars=20)
    for name in PUBLIC_METHODS:
        assert callable(getattr(mapper, name)), f"{cls.__name__} missing method {name!r}"


@pytest.mark.parametrize("cls", MAPPER_CLASSES, ids=lambda c: c.__name__)
def test_mapper_has_public_attrs(cls):
    mapper = cls(datetime_array=_datetime_array(), max_bars=20)
    for name in PUBLIC_ATTRS:
        assert hasattr(mapper, name), f"{cls.__name__} missing attribute {name!r}"


# --- window resolution behaves identically (tests the private helper) ---

@pytest.mark.parametrize("cls", MAPPER_CLASSES, ids=lambda c: c.__name__)
def test_calc_window_max_bars(cls):
    mapper = cls(datetime_array=_datetime_array(100), max_bars=20)
    w = mapper._calc_window()
    assert w.stop - w.start == 20


@pytest.mark.parametrize("cls", MAPPER_CLASSES, ids=lambda c: c.__name__)
def test_calc_window_start_end(cls):
    dt = _datetime_array(100)
    mapper = cls(datetime_array=dt, start=dt[10], end=dt[30])
    w = mapper._calc_window()
    assert w.start == 10
    assert w.stop == 31  # end side="right"


def test_both_mappers_agree_on_window():
    dt = _datetime_array(100)
    kwargs = dict(datetime_array=dt, start=dt[5], end=dt[80], max_bars=30)
    assert DateIndexMapper(**kwargs)._calc_window() == RawDateMapper(**kwargs)._calc_window()


def test_calc_window_is_not_public():
    """Regression: calc_window should not leak into the public API."""
    m = DateIndexMapper(datetime_array=_datetime_array())
    assert not hasattr(m, "calc_window"), "calc_window is private (_calc_window)"


# --- semantic differences: x-coordinate types ---

def test_date_index_rownum_is_integer():
    m = DateIndexMapper(datetime_array=_datetime_array(50))
    assert m.rownum.dtype.kind == "i"
    assert m.rownum[0] == 0
    assert m.rownum[-1] == 49


def test_raw_date_rownum_is_datetime():
    m = RawDateMapper(datetime_array=_datetime_array(50))
    assert m.rownum.dtype == np.dtype("datetime64[ns]")
    np.testing.assert_array_equal(m.rownum, m.datetime_array)


def test_series_xy_date_index_returns_integer_xs():
    dt = _datetime_array(50)
    x, y = DateIndexMapper(datetime_array=dt, max_bars=10).series_xy(np.arange(50))
    assert x.dtype.kind == "i"
    assert len(x) == len(y) == 10


def test_series_xy_raw_date_returns_datetime_xs():
    dt = _datetime_array(50)
    x, y = RawDateMapper(datetime_array=dt, max_bars=10).series_xy(np.arange(50))
    assert x.dtype == np.dtype("datetime64[ns]")
    assert len(x) == len(y) == 10


@pytest.mark.parametrize("cls", MAPPER_CLASSES, ids=lambda c: c.__name__)
def test_series_xy_variadic(cls):
    """Multiple value arrays can be sliced in one call."""
    dt = _datetime_array(50)
    mapper = cls(datetime_array=dt, max_bars=10)
    y1 = np.arange(50, dtype=float)
    y2 = np.arange(50, 100, dtype=float)
    xs, s1, s2 = mapper.series_xy(y1, y2)
    assert len(xs) == len(s1) == len(s2) == 10
    np.testing.assert_array_equal(s1, y1[-10:])
    np.testing.assert_array_equal(s2, y2[-10:])


def test_map_date_date_index_returns_int():
    dt = _datetime_array(50)
    out = DateIndexMapper(datetime_array=dt).map_date(dt[10])
    assert isinstance(out, int)
    assert out == 10


def test_map_date_raw_date_returns_datetime():
    dt = _datetime_array(50)
    out = RawDateMapper(datetime_array=dt).map_date(dt[10])
    assert isinstance(out, np.datetime64)
    assert out == dt[10]


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
    assert isinstance(chart.mapper, RawDateMapper)
    chart.plot(Candlesticks(), SMA(20) @ LinePlot())
    assert chart.count_axes() > 0
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
    assert isinstance(chart.mapper, RawDateMapper)
    chart.plot(SMA(20))                                  # implicit AutoPlot
    chart.plot(SMA(50) @ AutoPlot(label="trend"))        # AutoPlot override
    assert chart.count_axes() > 0
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
    assert chart.count_axes() > 0
    plt.close()


def test_chart_default_mode_uses_date_index_mapper():
    pytest.importorskip("polars")
    from mplchart.chart import Chart
    from mplchart.samples import sample_prices

    prices = sample_prices(freq="daily", backend="polars")
    chart = Chart(prices, max_bars=100)
    assert isinstance(chart.mapper, DateIndexMapper)
    plt.close()
