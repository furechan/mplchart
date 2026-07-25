"""Point & Figure tests — calc columns and primitive rendering — both backends."""

import numpy as np
import pytest
import matplotlib.pyplot as plt

from matplotlib.collections import EllipseCollection, LineCollection

from mplchart.chart import Chart
from mplchart.samples import sample_prices
from mplchart.styles import Styler
from mplchart.primitives import Candlesticks, PointFigure
from mplchart.primitives.pointfigure import calc_pnf
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


def test_calc_columns(backend):
    # X column 10->13, 3-box reversal into an O column 12->9
    prices = make_prices(
        backend,
        ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
        close=[10.0, 12.0, 13.0, 10.0, 9.0],
        volume=[10.0, 10.0, 10.0, 10.0, 10.0],
    )
    columns = calc_pnf(prices, box_size=1.0, reversal=3)

    assert detect_backend(columns) == backend
    assert len(columns) == 2

    # X column: up row; O column: down row — direction is close vs open
    assert columns["open"].to_numpy() == pytest.approx([10.0, 12.0])
    assert columns["close"].to_numpy() == pytest.approx([13.0, 9.0])
    assert columns["high"].to_numpy() == pytest.approx([13.0, 12.0])
    assert columns["low"].to_numpy() == pytest.approx([10.0, 9.0])

    # per-bar rate: X lived bars 0-3 (40 vol / 4 bars), O bar 4 (10 / 1)
    assert columns["volume"].to_numpy() == pytest.approx([10.0, 10.0])

    dates = columns["date"].to_numpy() if backend == "polars" else columns.index.to_numpy()
    assert dates.tolist() == np.array(["2024-01-02", "2024-01-04"], dtype="datetime64[ns]").tolist()


def test_pointfigure_primitive(backend):
    prices = sample_prices(freq="daily", backend=backend)
    chart = Chart(prices, max_bars=40, figsize=(6, 4))
    chart.plot(PointFigure(box_size=5.0))

    assert len(chart.view.prices) < len(prices)  # view holds columns, not bars
    kinds = {type(c) for c in chart.canvas.main_axes().collections}
    assert LineCollection in kinds  # X glyphs
    assert EllipseCollection in kinds  # O glyphs
    plt.close(chart.figure)


def test_pointfigure_settings_colors(backend):
    prices = sample_prices(freq="daily", backend=backend)
    style = Styler(settings={"pnf.up.color": "blue"})
    chart = Chart(prices, max_bars=40, figsize=(6, 4), style=style)
    chart.plot(PointFigure(box_size=5.0))

    xs = next(c for c in chart.canvas.main_axes().collections if type(c) is LineCollection)
    import matplotlib.colors as mcolors

    assert tuple(xs.get_color()[0]) == mcolors.to_rgba("blue")
    plt.close(chart.figure)


def test_pointfigure_must_touch_view_first(backend):
    prices = sample_prices(freq="daily", backend=backend)
    chart = Chart(prices, max_bars=40, figsize=(6, 4))
    with pytest.raises(ValueError, match="already created"):
        chart.plot([Candlesticks(), PointFigure(box_size=5.0)])
    plt.close(chart.figure)
