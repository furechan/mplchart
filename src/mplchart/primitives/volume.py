"""Volume primitive

Style settings consumed by this primitive:

    volume.up.color        up bars, close ≥ open (default: ~green)
    volume.down.color      down bars (default: ~red)
    volume.ma.color        SMA overlay line (default: ~gray)
    volume.alpha           opacity, bars and ma line (default: 0.5)
    volume.use_prev_close  interbar-coloring flag (default: False)

Each kwarg overrides its own setting (kwarg → setting → snapped default) —
independent per-element params, not an atomic scheme.
"""

import numpy as np

from ..model.primitive import Primitive
from ..utils import col_to_numpy, plot_vbars


class Volume(Primitive):
    """Volume primitive.

    Plots volume bars colored by bar direction — close ≥ open, matching the
    candlesticks, or close vs previous close with ``use_prev_close``. When
    the current pane already has content, volume rides
    a twinx overlay squashed at the bottom so it does not affect the price
    axis; an empty current pane (volume-only chart, or right after
    ``Pane``) is owned outright — full height, visible scale. An optional
    SMA of volume can be overlaid.

    Args:
        sma (int, optional): Period for the volume SMA overlay. Omit to skip
            the moving average line.
        width (float): Width of each volume bar as a fraction of bar spacing.
            Defaults to 0.8.
        alpha (float, optional): Opacity of the bars and ma line, between
            0.0 and 1.0. Defaults to the ``volume.alpha`` setting, else 0.5.
        colorup (str, optional): Color for up-bars. Defaults to the
            ``volume.up.color`` setting, else green (prop-cycle snapped).
        colordn (str, optional): Color for down-bars. Defaults to the
            ``volume.down.color`` setting, else red (prop-cycle snapped).
        colorma (str, optional): Color for the SMA overlay line. Defaults to
            the ``volume.ma.color`` setting, else gray (prop-cycle snapped).
        use_prev_close (bool, optional): Color bars by close vs previous
            close (interbar) instead of close vs open (intrabar). Default
            (``None``) defers to the ``volume.use_prev_close`` setting,
            else ``False``. Mirrors the flag of the same name on
            ``Candlesticks``.
    """

    def __init__(
        self,
        sma: int | None = None,
        *,
        width: float = 0.8,
        alpha: float | None = None,
        colorup: str | None = None,
        colordn: str | None = None,
        colorma: str | None = None,
        use_prev_close: bool | None = None,
    ):
        self.sma = sma
        self.width = width
        self.alpha = alpha
        self.colorup = colorup
        self.colordn = colordn
        self.colorma = colorma
        self.use_prev_close = use_prev_close

    def __str__(self):
        return self.__class__.__name__

    def apply_to_chart(self, chart):
        # an empty current pane resolves as its own overlay (volume-only
        # charts, or right after Pane) — owned outright, full height,
        # visible scale; a pane with content yields a squashed twin
        ax = chart.canvas.get_axes("twinx")

        prices = chart.view.slice(chart.view.prices, xcol="xloc")
        volume = col_to_numpy(prices, "volume")
        open_ = col_to_numpy(prices, "open")
        close = col_to_numpy(prices, "close")

        xv = col_to_numpy(prices, "xloc")

        width = self.width
        alpha = chart.canvas.get_setting("volume", "alpha", override=self.alpha, fallback=0.5)

        # per-element chain: kwarg → setting → snapped default (independent
        # params, not an atomic scheme — same policy as OHLC)
        resolve = chart.canvas.resolve_color
        colorup = resolve("volume.up", ax, override=self.colorup, fallback="~green")
        colordn = resolve("volume.down", ax, override=self.colordn, fallback="~red")

        # direction: intrabar (close vs open, matching the candlesticks) by
        # default, or interbar with use_prev_close — first bar compares to itself
        use_prev_close = chart.canvas.get_setting(
            "volume", "use_prev_close", override=self.use_prev_close, fallback=False
        )
        if use_prev_close:
            prev = np.concatenate((close[:1], close[:-1]))
            up = close >= prev
        else:
            up = close >= open_

        color = np.where(up, colorup, colordn)

        if ax._label == "twinx":
            vmax = volume.max()
            ax.set_ylim(0.0, vmax * 4.0)
            ax.yaxis.set_visible(False)

        plot_vbars(ax, xv, volume, width=width, alpha=alpha, color=color)

        if self.sma:
            colorma = resolve("volume.ma", ax, override=self.colorma, fallback="~gray")
            n = self.sma
            valid = np.convolve(volume, np.ones(n) / n, mode="valid")
            average = np.concatenate([np.full(n - 1, np.nan), valid])
            ax.plot(xv, average, linewidth=0.7, alpha=alpha, color=colorma)
