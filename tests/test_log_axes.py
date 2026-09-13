"""Collection limits must remain in price coordinates on logarithmic axes."""

import matplotlib.pyplot as plt
import pytest

from mplchart.chart import Chart
from mplchart.primitives import Bars, Candlesticks, OHLC, PointFigure
from mplchart.samples import sample_prices


@pytest.mark.parametrize("backend", ["pandas", "polars"])
@pytest.mark.parametrize("raw_dates", [False, True])
@pytest.mark.parametrize("renderer", ["candles", "ohlc", "bars", "pnf"])
def test_collection_log_limits(backend, raw_dates, renderer):
    pytest.importorskip(backend)
    if renderer == "pnf" and raw_dates:
        pytest.skip("PointFigure transforms require row-number dates")
    primitive = {
        "candles": Candlesticks(), "ohlc": OHLC(),
        "bars": Bars("close"), "pnf": PointFigure(box_size=5),
    }[renderer]
    prices = sample_prices(backend=backend).tail(500)
    chart = Chart(prices, max_bars=40, raw_dates=raw_dates, yaxis_log=True)
    try:
        chart.plot(primitive)
        ax = chart.canvas.main_axes()
        if renderer == "bars":
            _, values = chart.view.series_xy(chart.view.eval("close"))
            low, high = min(values), max(values)
            assert ax.dataLim.ymin == 0
            assert ax.dataLim.minposy == pytest.approx(low)
        else:
            _, lows = chart.view.series_xy(chart.view.eval("low"))
            _, highs = chart.view.series_xy(chart.view.eval("high"))
            low, high = min(lows), max(highs)
            assert ax.dataLim.ymin == pytest.approx(low)
        assert ax.dataLim.ymax == pytest.approx(high)
        margin = ax.get_ymargin()
        ratio = high / low
        expected = (low / ratio**margin, high * ratio**margin)
        assert ax.get_ylim() == pytest.approx(expected)
        assert b"<svg" in chart.render()
        assert ax.get_ylim() == pytest.approx(expected)
    finally:
        plt.close(chart.figure)
