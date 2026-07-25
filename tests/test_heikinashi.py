"""Tests for the HeikinAshi primitive (Candlesticks variant)."""

import numpy as np
import pytest
import matplotlib.pyplot as plt

from mplchart.chart import Chart
from mplchart.primitives import Candlesticks, HeikinAshi
from mplchart.primitives.heikinashi import calc_heikin_ashi

pd = pytest.importorskip("pandas")


def make_prices():
    return pd.DataFrame(
        {
            "open": [10.0, 11.0, 10.0],
            "high": [11.5, 11.5, 10.5],
            "low": [9.5, 9.5, 9.5],
            "close": [11.0, 10.0, 10.0],
            "volume": [100, 100, 100],
        },
        index=pd.date_range("2024-01-01", periods=3, freq="D"),
    )


def check_heikin_ashi(result, open_, high, low, close):
    """Verify Heikin-Ashi values against the defining formulas."""
    ha_close = (open_ + high + low + close) / 4

    assert result["close"].to_numpy() == pytest.approx(ha_close)

    ha_open = result["open"].to_numpy()
    assert ha_open[0] == pytest.approx((open_[0] + close[0]) / 2)
    for i in range(1, len(ha_open)):
        assert ha_open[i] == pytest.approx((ha_open[i - 1] + ha_close[i - 1]) / 2)

    ha_high = result["high"].to_numpy()
    ha_low = result["low"].to_numpy()
    assert np.all(ha_high >= np.maximum(ha_open, ha_close))
    assert np.all(ha_low <= np.minimum(ha_open, ha_close))
    assert np.all(ha_high >= high)
    assert np.all(ha_low <= low)


def test_calc_heikin_ashi_pandas():
    prices = make_prices()
    result = calc_heikin_ashi(prices)

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["open", "high", "low", "close"]
    assert result.index.equals(prices.index)

    check_heikin_ashi(
        result,
        prices["open"].to_numpy(), prices["high"].to_numpy(),
        prices["low"].to_numpy(), prices["close"].to_numpy(),
    )


def test_calc_heikin_ashi_polars():
    pl = pytest.importorskip("polars")
    prices = pl.DataFrame(pd.DataFrame(make_prices()).reset_index(names="date"))
    result = calc_heikin_ashi(prices)

    assert isinstance(result, pl.DataFrame)
    assert result.columns == ["open", "high", "low", "close"]

    check_heikin_ashi(
        result,
        prices["open"].to_numpy(), prices["high"].to_numpy(),
        prices["low"].to_numpy(), prices["close"].to_numpy(),
    )


def test_heikin_ashi_renders():
    prices = make_prices()
    chart = Chart(prices, figsize=(4, 3))
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


def test_heikin_ashi_label():
    chart = Chart(make_prices(), figsize=(4, 3))
    chart.plot(HeikinAshi(label="HA"))
    wicks, poly = chart.canvas.main_axes().collections
    assert poly.get_label() == "HA"
    plt.close(chart.figure)


def test_use_prev_close_pinned():
    # interbar coloring is a regular-candle concept — pinned intrabar for ha
    # bars (False beats the candle.use_prev_close setting, which defers on
    # None only)
    assert HeikinAshi().use_prev_close is False
    with pytest.raises(TypeError):
        HeikinAshi(use_prev_close=True)  # ty: ignore[unknown-argument]  # pyright: ignore[reportCallIssue]


def test_calc_as_plain_indicator():
    # the calc binds to Candlesticks directly; label derives from the function name
    chart = Chart(make_prices(), figsize=(4, 3))
    chart.plot(Candlesticks(calc_heikin_ashi))
    wicks, poly = chart.canvas.main_axes().collections
    assert poly.get_label() == "calc_heikin_ashi"
    plt.close(chart.figure)
