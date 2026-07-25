"""Renko tests — calc bricks and primitive rendering — both backends."""

import numpy as np
import pytest
import matplotlib.pyplot as plt

from mplchart.chart import Chart
from mplchart.samples import sample_prices
from mplchart.primitives import Candlesticks, Renko
from mplchart.primitives.renko import calc_renko
from mplchart.utils import detect_backend


@pytest.fixture(params=["pandas", "polars"])
def backend(request):
    pytest.importorskip(request.param)
    return request.param


def make_prices(backend, dates, close, volume):
    """tiny OHLCV frame in the requested backend (high/low bracket the close)"""
    close = np.asarray(close, dtype=float)
    data = dict(
        open=close, high=close + 0.1, low=close - 0.1, close=close,
        volume=np.asarray(volume, dtype=float),
    )
    dates = np.array(dates, dtype="datetime64[ns]")
    if backend == "pandas":
        import pandas as pd

        return pd.DataFrame(data, index=pd.DatetimeIndex(dates, name="date"))
    import polars as pl

    return pl.DataFrame({"date": dates, **data})


def test_calc_bricks(backend):
    # closes: two up bricks on one bar, then a down brick (2-brick reversal)
    prices = make_prices(
        backend,
        ["2024-01-01", "2024-01-02", "2024-01-03"],
        close=[10.0, 12.5, 9.5],
        volume=[1.0, 10.0, 100.0],
    )
    bricks = calc_renko(prices, brick_size=1.0)

    assert detect_backend(bricks) == backend
    assert len(bricks) == 3
    assert bricks["open"].to_numpy() == pytest.approx([10.0, 11.0, 11.0])
    assert bricks["close"].to_numpy() == pytest.approx([11.0, 12.0, 10.0])
    assert bricks["high"].to_numpy() == pytest.approx([11.0, 12.0, 11.0])
    assert bricks["low"].to_numpy() == pytest.approx([10.0, 11.0, 10.0])

    # volume since previous brick, shared evenly across same-bar bricks
    assert bricks["volume"].to_numpy() == pytest.approx([5.5, 5.5, 100.0])


def test_same_bar_bricks_nudged(backend):
    prices = make_prices(
        backend,
        ["2024-01-01", "2024-01-02"],
        close=[10.0, 13.5],  # one bar completes three bricks
        volume=[1.0, 9.0],
    )
    bricks = calc_renko(prices, brick_size=1.0)
    dates = bricks["date"].to_numpy() if backend == "polars" else bricks.index.to_numpy()

    assert len(bricks) == 3
    assert len(np.unique(dates)) == 3  # +1ns nudge keeps timestamps unique
    assert (np.diff(dates) == np.timedelta64(1, "ns")).all()


def test_renko_primitive(backend):
    prices = sample_prices(freq="daily", backend=backend)
    chart = Chart(prices, max_bars=100, figsize=(6, 4))
    chart.plot(Renko(brick_size=5.0))

    assert len(chart.view.prices) < len(prices)  # view holds bricks, not bars
    wicks, poly = chart.canvas.main_axes().collections
    assert poly.get_label() == "Renko"
    plt.close(chart.figure)


def test_renko_must_touch_view_first(backend):
    prices = sample_prices(freq="daily", backend=backend)
    chart = Chart(prices, max_bars=100, figsize=(6, 4))
    with pytest.raises(ValueError, match="already created"):
        chart.plot([Candlesticks(), Renko(brick_size=5.0)])
    plt.close(chart.figure)


def test_renko_raw_dates_raises(backend):
    prices = sample_prices(freq="daily", backend=backend)
    chart = Chart(prices, raw_dates=True, figsize=(6, 4))
    with pytest.raises(ValueError, match="raw_dates"):
        chart.plot(Renko(brick_size=5.0))
    plt.close(chart.figure)


def test_use_prev_close_pinned():
    assert Renko().use_prev_close is False
    with pytest.raises(TypeError):
        Renko(use_prev_close=True)  # ty: ignore[unknown-argument]  # pyright: ignore[reportCallIssue]
