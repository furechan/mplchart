"""Renko primitive"""

import numpy as np

from ..utils import col_to_numpy, get_dates, wrap_result
from .candlesticks import Candlesticks


def calc_renko(prices, brick_size=None):
    """Compute Renko bricks from a prices frame — one row per brick.

    Close-based bricks with the classic 2-brick reversal, expressed as one
    symmetric rule over the last brick's top/bottom: an up brick lays when
    close reaches ``top + size``, a down brick when close reaches
    ``bottom - size``. The seed snaps the first close to the brick grid.

    Returns an OHLCV frame in the source backend, dated by brick completion:
    ``open``/``close`` are the brick bottom/top (directional), ``high``/``low``
    coincide with them, and volume accumulated since the previous brick is
    shared evenly across the bricks a bar completes. Same-bar bricks are
    nudged +1ns apart so date-aligned slicing stays one-to-one.

    Args:
        brick_size (float, optional): Brick height in price units. Defaults
            to the mean true range of the data.
    """
    dates = get_dates(prices)
    high = col_to_numpy(prices, "high")
    low = col_to_numpy(prices, "low")
    close = col_to_numpy(prices, "close")
    volume = col_to_numpy(prices, "volume")

    if brick_size is None:
        prev = np.concatenate((close[:1], close[:-1]))
        tr = np.maximum(high - low, np.maximum(np.abs(high - prev), np.abs(low - prev)))
        brick_size = float(np.nanmean(tr))

    size = float(brick_size)

    # seed: first close snapped to the brick grid, zero-height anchor
    top = bottom = round(close[0] / size) * size

    idx, opens, closes, vols = [], [], [], []
    accum = float(volume[0])

    for i in range(1, len(close)):
        accum += float(volume[i])
        emitted = 0
        while close[i] >= top + size:  # up brick
            opens.append(top)
            closes.append(top + size)
            bottom, top = top, top + size
            idx.append(i)
            emitted += 1
        while close[i] <= bottom - size:  # down brick
            opens.append(bottom)
            closes.append(bottom - size)
            top, bottom = bottom, bottom - size
            idx.append(i)
            emitted += 1
        if emitted:
            vols.extend([accum / emitted] * emitted)
            accum = 0.0

    opens = np.array(opens, dtype=float)
    closes = np.array(closes, dtype=float)
    idx = np.array(idx, dtype=int)

    # nudge same-bar bricks +1ns each: pandas date-aligned slicing goes
    # cartesian on duplicate dates — unique timestamps keep it one-to-one;
    # the offset is invisible in date labels
    rank = np.arange(len(idx)) - np.searchsorted(idx, idx)
    brick_dates = dates[idx].astype("datetime64[ns]") + rank * np.timedelta64(1, "ns")

    result = dict(
        open=opens,
        high=np.maximum(opens, closes),
        low=np.minimum(opens, closes),
        close=closes,
        volume=np.array(vols, dtype=float),
    )
    return wrap_result(result, prices, dates=brick_dates)


class Renko(Candlesticks):
    """Renko primitive.

    Plots Renko bricks computed from the chart prices — binds
    :func:`calc_renko` as the chart prices transform via
    ``chart.get_view(transform=...)``, then renders through Candlesticks
    with touching, full-width bodies (bricks have no wicks).

    Must be the first primitive to touch the chart view — plot it first;
    anything plotted before it fixes the untransformed view and the late
    transform raises. The chart windowing (``max_bars`` etc.) operates in
    brick space. Incompatible with ``raw_dates``.

    Accepts the Candlesticks styling arguments (color schemes, ``candle.*``
    settings, label) except ``use_prev_close``, which is pinned intrabar:
    brick direction is close vs open by construction.

    Args:
        brick_size (float, optional): Brick height in price units. Defaults
            to the mean true range of the data.
    """

    def __init__(
        self,
        brick_size: float | None = None,
        *,
        label: str = "Renko",
        width: float = 1.0,
        alpha: float | None = None,
        color: str | None = None,
        colorup: str | None = None,
        colordn: str | None = None,
        hollow: bool | None = None,
    ):
        super().__init__(
            label=label,
            width=width,
            alpha=alpha,
            color=color,
            colorup=colorup,
            colordn=colordn,
            hollow=hollow,
            use_prev_close=False,
        )
        self.brick_size = brick_size

    def transform(self, prices):
        return calc_renko(prices, brick_size=self.brick_size)

    def apply_to_chart(self, chart):
        chart.get_view(transform=self.transform)
        super().apply_to_chart(chart)
