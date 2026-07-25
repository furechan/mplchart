"""Tests for the HeikinAshi primitive (Candlesticks variant) — both backends."""

import numpy as np
import pytest
import matplotlib.pyplot as plt

from mplchart.chart import Chart
from mplchart.samples import sample_prices
from mplchart.primitives import Candlesticks, HeikinAshi
from mplchart.primitives.heikinashi import calc_heikin_ashi
from mplchart.utils import detect_backend


@pytest.fixture(params=["pandas", "polars"])
def backend(request):
    pytest.importorskip(request.param)
    return request.param


@pytest.fixture
def prices(backend):
    return sample_prices(freq="daily", backend=backend).tail(50)


def test_calc_heikin_ashi(backend, prices):
    # frame in, frame out — the result stays in the source backend
    result = calc_heikin_ashi(prices)

    assert detect_backend(result) == backend
    assert list(result.columns) == ["open", "high", "low", "close"]
    assert len(result) == len(prices)
    if backend == "pandas":
        assert result.index.equals(prices.index)

    open_, high, low, close = (prices[c].to_numpy() for c in ("open", "high", "low", "close"))
    ha_open, ha_close = result["open"].to_numpy(), result["close"].to_numpy()

    assert ha_close == pytest.approx((open_ + high + low + close) / 4)
    assert ha_open[0] == pytest.approx((open_[0] + close[0]) / 2)
    assert ha_open[1:] == pytest.approx((ha_open[:-1] + ha_close[:-1]) / 2)
    assert result["high"].to_numpy() == pytest.approx(np.maximum(high, np.maximum(ha_open, ha_close)))
    assert result["low"].to_numpy() == pytest.approx(np.minimum(low, np.minimum(ha_open, ha_close)))


def test_heikin_ashi_renders(prices):
    chart = Chart(prices, figsize=(6, 4))
    chart.plot(HeikinAshi())
    wicks, poly = chart.canvas.main_axes().collections
    assert poly.get_label() == "HeikinAshi"

    ha = calc_heikin_ashi(prices)
    ha_open = ha["open"].to_numpy()
    ha_close = ha["close"].to_numpy()

    # body rectangles span the computed ha open/close per bar
    for i, path in enumerate(poly.get_paths()):
        ys = path.vertices[:, 1]
        assert ys.min() == pytest.approx(min(ha_open[i], ha_close[i]))
        assert ys.max() == pytest.approx(max(ha_open[i], ha_close[i]))

    plt.close(chart.figure)


def test_heikin_ashi_label(prices):
    chart = Chart(prices, figsize=(6, 4))
    chart.plot(HeikinAshi(label="HA"))
    wicks, poly = chart.canvas.main_axes().collections
    assert poly.get_label() == "HA"
    plt.close(chart.figure)


def test_calc_as_plain_indicator(prices):
    # the calc binds to Candlesticks directly; label derives from the function name
    chart = Chart(prices, figsize=(6, 4))
    chart.plot(Candlesticks(calc_heikin_ashi))
    wicks, poly = chart.canvas.main_axes().collections
    assert poly.get_label() == "calc_heikin_ashi"
    plt.close(chart.figure)


def test_use_prev_close_pinned():
    # interbar coloring is a regular-candle concept — pinned intrabar for ha
    # bars (False beats the candle.use_prev_close setting, which defers on
    # None only)
    assert HeikinAshi().use_prev_close is False
    with pytest.raises(TypeError):
        HeikinAshi(use_prev_close=True)  # ty: ignore[unknown-argument]  # pyright: ignore[reportCallIssue]
