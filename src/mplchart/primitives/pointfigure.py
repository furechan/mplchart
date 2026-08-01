"""Point & Figure primitive"""

import numpy as np

from matplotlib.collections import EllipseCollection, LineCollection

from ..model.primitive import Primitive
from ..utils import col_to_numpy, get_dates, wrap_result


def calc_pnf(prices, box_size=None, reversal=3):
    """Compute Point & Figure columns from a prices frame — one row per column.

    Close-based with an n-box reversal: an X column extends up one box at a
    time while close reaches ``top + box``; it reverses when close falls
    ``reversal * box`` below the top, closing the column and opening an O
    column one box below (and symmetrically for O to X). The seed waits for
    the first one-box move to pick a direction.

    Returns an OHLCV frame in the source backend, dated by column start
    (start dates are strictly increasing — one close cannot reverse twice):
    X columns are up rows (``open=bottom, close=top``), O columns down rows;
    ``high``/``low`` are the column extremes on the box grid; volume is a
    per-bar rate — mean bar volume over the column lifetime, a participation
    measure independent of box size and column height.

    Args:
        box_size (float, optional): Box height in price units. Defaults to
            the mean true range of the data.
        reversal (int): Boxes of adverse movement required to reverse the
            column. Defaults to 3.
    """
    dates = get_dates(prices)
    high = col_to_numpy(prices, "high")
    low = col_to_numpy(prices, "low")
    close = col_to_numpy(prices, "close")
    volume = col_to_numpy(prices, "volume")

    if box_size is None:
        prev = np.concatenate((close[:1], close[:-1]))
        tr = np.maximum(high - low, np.maximum(np.abs(high - prev), np.abs(low - prev)))
        box_size = float(np.nanmean(tr))

    size = float(box_size)

    tops, bottoms, dirs, idx, vols = [], [], [], [], []

    def emit(top, bottom, trend, start, vol, nbars):
        tops.append(top)
        bottoms.append(bottom)
        dirs.append(trend)
        idx.append(start)
        vols.append(vol / max(1, nbars))

    top = bottom = round(close[0] / size) * size
    trend, start = 0, 0
    accum, nbars = float(volume[0]), 1

    for i in range(1, len(close)):
        accum += float(volume[i])
        nbars += 1
        c = close[i]

        if trend == 0:
            # seed: the first one-box move sets the direction
            if c >= top + size:
                top += size * int((c - top) // size)
                trend, start = 1, i
            elif c <= bottom - size:
                bottom -= size * int((bottom - c) // size)
                trend, start = -1, i
        elif trend > 0:
            if c >= top + size:  # extend X column
                top += size * int((c - top) // size)
            elif c <= top - reversal * size:  # reverse to O
                emit(top, bottom, 1, start, accum, nbars)
                accum, nbars = 0.0, 0
                bottom = top - size * int((top - c) // size)
                top, trend, start = top - size, -1, i
        else:
            if c <= bottom - size:  # extend O column
                bottom -= size * int((bottom - c) // size)
            elif c >= bottom + reversal * size:  # reverse to X
                emit(top, bottom, -1, start, accum, nbars)
                accum, nbars = 0.0, 0
                top = bottom + size * int((c - bottom) // size)
                bottom, trend, start = bottom + size, 1, i

    if trend != 0:  # final open column
        emit(top, bottom, trend, start, accum, nbars)

    top_arr = np.array(tops, dtype=float)
    bottom_arr = np.array(bottoms, dtype=float)
    up = np.array(dirs) > 0

    result = dict(
        open=np.where(up, bottom_arr, top_arr),
        high=top_arr,
        low=bottom_arr,
        close=np.where(up, top_arr, bottom_arr),
        volume=np.array(vols, dtype=float),
    )
    return wrap_result(result, prices, dates=dates[np.array(idx, dtype=int)])


class PointFigure(Primitive):
    """Point & Figure primitive.

    Plots Point & Figure columns computed from the chart prices — binds
    :func:`calc_pnf` as the chart prices transform via
    ``chart.get_view(transform=...)``, then draws X's (rising columns) and
    O's (falling columns) on the box grid.

    Must be the first primitive to touch the chart view — plot it first;
    anything plotted before it fixes the untransformed view and the late
    transform raises. The chart windowing (``max_bars`` etc.) operates in
    column space. Incompatible with ``raw_dates``.

    Args:
        box_size (float, optional): Box height in price units. Defaults to
            the mean true range of the data. Also sizes the glyph grid —
            when None, the render grid is inferred from the column levels.
        reversal (int): Boxes of adverse movement required to reverse the
            column. Defaults to 3.
        width (float): Glyph width as a fraction of column spacing.
            Defaults to 0.8.
        alpha (float, optional): Opacity of the glyphs.
        colorup (str, optional): X-column color. Defaults to the ``pnf.up``
            setting, else green.
        colordn (str, optional): O-column color. Defaults to the ``pnf.down``
            setting, else red.
        label (str): legend label. Defaults to "PnF".
    """

    def __init__(
        self,
        box_size: float | None = None,
        reversal: int = 3,
        *,
        width: float = 0.8,
        alpha: float | None = None,
        colorup: str | None = None,
        colordn: str | None = None,
        label: str = "PnF",
    ):
        self.box_size = box_size
        self.reversal = reversal
        self.width = width
        self.alpha = alpha
        self.colorup = colorup
        self.colordn = colordn
        self.label = label

    def __str__(self):
        return self.__class__.__name__

    def transform(self, prices):
        return calc_pnf(prices, box_size=self.box_size, reversal=self.reversal)

    def apply_to_chart(self, chart):
        chart.get_view(transform=self.transform)

        ax = chart.canvas.get_axes()

        prices = chart.view.slice(chart.view.prices, xcol="xloc")
        xv = col_to_numpy(prices, "xloc").astype(float)
        open_ = col_to_numpy(prices, "open")
        high = col_to_numpy(prices, "high")
        low = col_to_numpy(prices, "low")
        close = col_to_numpy(prices, "close")

        resolve = chart.canvas.resolve_color
        colorup = resolve("pnf.up", ax=ax, override=self.colorup, fallback="green")
        colordn = resolve("pnf.down", ax=ax, override=self.colordn, fallback="red")

        box = self.box_size
        if box is None:  # infer from the grid: smallest gap between levels
            levels = np.unique(np.round(np.concatenate([high, low]), 9))
            gaps = np.diff(levels)
            box = float(gaps[gaps > 1e-9].min())

        spacing = float(np.nanmin(np.diff(xv))) if len(xv) > 1 else 1.0
        w = spacing * self.width

        up = close >= open_
        xsegs, centers = [], []
        for x, hi, lo, u in zip(xv, high, low, up):
            for k in range(max(1, int(round((hi - lo) / box)))):
                y = lo + k * box
                if u:
                    x0, x1 = x - w * 0.4, x + w * 0.4
                    y0, y1 = y + box * 0.1, y + box * 0.9
                    xsegs.append([(x0, y0), (x1, y1)])
                    xsegs.append([(x0, y1), (x1, y0)])
                else:
                    centers.append((x, y + box / 2))

        if xsegs:
            xs = LineCollection(
                np.array(xsegs),  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # stubs say Sequence[ArrayLike]; 3-D ndarray is supported
                colors=colorup, linewidths=1.2,
                alpha=self.alpha, label=self.label,
            )
            ax.add_collection(xs)
        if centers:
            os_ = EllipseCollection(
                widths=w * 0.8, heights=box * 0.8, angles=0, units="xy",
                offsets=np.array(centers), offset_transform=ax.transData,
                facecolors="none", edgecolors=colordn,
                linewidths=1.2, alpha=self.alpha,
            )
            ax.add_collection(os_)

        pts = np.column_stack([np.concatenate([xv, xv]), np.concatenate([low, high])])
        ax.update_datalim(pts)
        ax.autoscale_view()
