"""Heikin-Ashi primitive"""

import numpy as np

from .candlesticks import Candlesticks
from ..utils import col_to_numpy, wrap_result


def calc_heikin_ashi(prices):
    """Compute Heikin-Ashi bars from an OHLC prices frame.

    The Heikin-Ashi close is the bar average ``(open + high + low + close) / 4``
    and the open is the midpoint of the previous Heikin-Ashi bar, seeded with
    the first bar's ``(open + close) / 2``. High and low envelope the raw
    extremes and the computed open/close.

    Computes in numpy and returns a frame matching the source backend, with
    ``open``, ``high``, ``low``, ``close`` columns.
    """
    open_ = col_to_numpy(prices, "open")
    high = col_to_numpy(prices, "high")
    low = col_to_numpy(prices, "low")
    close = col_to_numpy(prices, "close")

    ha_close = (open_ + high + low + close) / 4.0

    # ha_open is recursive (midpoint of the previous ha bar) — plain loop
    ha_open = np.empty_like(ha_close)
    if len(ha_open) > 0:
        ha_open[0] = (open_[0] + close[0]) / 2.0
        for i in range(1, len(ha_open)):
            ha_open[i] = (ha_open[i - 1] + ha_close[i - 1]) / 2.0

    ha_high = np.maximum(high, np.maximum(ha_open, ha_close))
    ha_low = np.minimum(low, np.minimum(ha_open, ha_close))

    result = dict(open=ha_open, high=ha_high, low=ha_low, close=ha_close)
    return wrap_result(result, prices)


class HeikinAshi(Candlesticks):
    """Heikin-Ashi primitive.

    Plots Heikin-Ashi ("average bar") candles computed from the chart
    prices — a Candlesticks specialization bound to :func:`calc_heikin_ashi`.
    Accepts the Candlesticks styling arguments (color schemes, ``candle.*``
    settings, label) except ``use_prev_close``, which is pinned intrabar:
    Heikin-Ashi bars define their direction as ha close vs ha open.
    """

    def __init__(
        self,
        *,
        label: str = "HeikinAshi",
        width: float = 0.8,
        alpha: float | None = None,
        color: str | None = None,
        colorup: str | None = None,
        colordn: str | None = None,
        hollow: bool | None = None,
    ):
        super().__init__(
            calc_heikin_ashi,
            label=label,
            width=width,
            alpha=alpha,
            color=color,
            colorup=colorup,
            colordn=colordn,
            hollow=hollow,
            use_prev_close=False,
        )
