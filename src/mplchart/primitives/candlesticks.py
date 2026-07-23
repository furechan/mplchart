"""Candlesticks primitive

Style settings consumed by this primitive (see notes/candlestick-styles.md):

    candle.up.color      up-bar faces (and default for edges → wicks)
    candle.down.color    down-bar faces (ditto)
    edge.up.color        body outlines (default: follow the faces)
    edge.down.color
    wicks.color          neutral wick color (default: follow the edges)
    candle.hollow.color  hollow-body fill (default: axes.facecolor)
    candle.alpha         opacity (default: 1.0)

Color kwargs bypass the color settings entirely (atomic schemes); an explicit
``alpha=`` kwarg wins over ``candle.alpha``.
"""

import warnings

import numpy as np

import matplotlib.pyplot as plt

from matplotlib.collections import LineCollection, PolyCollection

from ..model.primitive import Primitive
from ..utils import col_to_numpy, xvalues_to_float


class Candlesticks(Primitive):
    """Candlesticks primitive.

    Plots OHLC prices as a candlestick chart. Up-bars are close ≥ open.
    The color kwargs declare a complete scheme — schemes are atomic:

    - no color kwargs — style-driven: palette from the ``candle.*`` color
      settings, falling back to the default look (mono hollow: up-bars
      hollow, down-bars filled, in ``text.color``)
    - ``color=`` — mono hollow in the given color
    - ``colorup=`` / ``colordn=`` — filled bicolor
    - ``colorup=`` / ``colordn=`` with ``hollow=True`` — colored hollow
      (TradingView hollow candles)

    In the no-kwargs path, ``candle.up.color`` / ``candle.down.color`` select
    the filled bicolor family (missing side falls to ``text.color``),
    ``edge.up.color`` / ``edge.down.color`` override the body outlines,
    ``wicks.color`` gives neutral wicks (yahoo-style; wicks otherwise follow
    the edges), and ``candle.hollow.color`` sets the hollow-body fill
    (default ``axes.facecolor``). Color kwargs bypass settings entirely.

    Args:
        width (float): Width of each candlestick body as a fraction of bar
            spacing. Defaults to 0.8.
        alpha (float, optional): Opacity of the candlesticks, between 0.0
            and 1.0. Defaults to the ``candle.alpha`` setting, else 1.0.
        color (str, optional): Single color for the mono hollow scheme.
            Mutually exclusive with ``colorup``/``colordn``.
        colorup (str, optional): Color for up-bars (bicolor scheme).
            Defaults to the current ``text.color`` matplotlib parameter.
        colordn (str, optional): Color for down-bars (bicolor scheme).
            Defaults to the current ``text.color`` matplotlib parameter.
        hollow (bool, optional): Fill up-bodies with the background color
            (``axes.facecolor``) instead of the up color. Default (``None``)
            resolves from the palette — hollow when the resolved faces are
            mono, filled when they differ. ``False`` with an explicit mono
            ``color=`` raises at plot time (direction-blind). Combine with
            ``use_prev_close`` for the StockCharts look.
        use_prev_close (bool): Color bars by close vs previous close
            (interbar) instead of close vs open (intrabar). Meaningless for
            a mono palette — raises at plot time with an explicit
            ``color=``. Defaults to ``False``.
        use_bars (bool): Deprecated and ignored — the legacy bar renderer was
            removed (sample code preserved in
            ``playground/candlesticks-as-bars.ipynb``).
    """

    def __init__(
        self,
        *,
        width: float = 0.8,
        alpha: float | None = None,
        color: str | None = None,
        colorup: str | None = None,
        colordn: str | None = None,
        hollow: bool | None = None,
        use_prev_close: bool = False,
        use_bars: bool = False,
    ):
        if use_bars:
            warnings.warn(
                "use_bars is deprecated and ignored — the legacy bar renderer "
                "was removed",
                DeprecationWarning,
                stacklevel=2,
            )

        if color and (colorup or colordn):
            raise ValueError("Cannot pass color together with colorup/colordn!")

        self.width = width
        self.alpha = alpha
        self.color = color
        self.colorup = colorup
        self.colordn = colordn
        self.hollow = hollow
        self.use_prev_close = use_prev_close

    def __str__(self):
        return self.__class__.__name__

    def check_mono_flags(self):
        """Reject mode flags inconsistent with an explicit mono ``color=``.

        Params-only consistency — the default (settings-driven) mode is never
        validated: settings and defaults bend to the params, not the reverse.
        """
        if self.use_prev_close:
            raise ValueError("use_prev_close requires colorup/colordn!")
        if self.hollow is False:
            raise ValueError("Mono candles need hollow to show direction!")

    def apply_to_chart(self, chart):
        ax = chart.canvas.get_axes()

        prices = chart.view.slice(chart.view.prices, xcol="xloc")
        xvalues = np.asarray(prices["xloc"])

        label = str(self)
        width = self.width

        if self.alpha is not None:
            alpha = self.alpha
        else:
            alpha = chart.canvas.get_setting("candle", "alpha", fallback=1.0)

        resolve = chart.canvas.resolve_color
        textcolor = plt.rcParams["text.color"]
        facecolor = plt.rcParams["axes.facecolor"]

        # scheme selection — color kwargs declare an atomic scheme, sanitized
        # to two side colors up front; unset sides never fall to settings
        if self.colorup or self.colordn:
            # bicolor mode: missing side falls to textcolor
            if self.color:
                raise ValueError("Cannot pass color together with colorup/colordn!")
            colorup = self.colorup or textcolor
            colordn = self.colordn or textcolor
        elif self.color:
            # mono mode: one color, both sides
            self.check_mono_flags()
            colorup = colordn = self.color
        else:
            # default mode: no color kwargs
            colorup = colordn = None

        # single flow, one resolve per renderer slot; overrides are the
        # sanitized side colors, fallbacks chain faces → edges → wicks
        faceup = resolve("candle.up", ax, override=colorup, fallback=textcolor)
        facedn = resolve("candle.down", ax, override=colordn, fallback=textcolor)
        edgeup = resolve("edge.up", ax, override=colorup, fallback=faceup)
        edgedn = resolve("edge.down", ax, override=colordn, fallback=facedn)
        wickup = resolve("wicks", ax, override=colorup, fallback=edgeup)
        wickdn = resolve("wicks", ax, override=colordn, fallback=edgedn)

        hollow = self.hollow if self.hollow is not None else (faceup == facedn)

        if hollow:
            # kwarg schemes (colorup set) pin the hollow fill to the background
            faceoff = resolve("candle.hollow", ax, override=facecolor if colorup else None, fallback=facecolor)
        else:
            faceoff = None

        return plot_cspoly(
            prices, xvalues, ax=ax, width=width, alpha=alpha,
            faceup=faceup, facedn=facedn, edgeup=edgeup, edgedn=edgedn,
            wickup=wickup, wickdn=wickdn, faceoff=faceoff,
            use_prev_close=self.use_prev_close,
            label=label,
        )


def plot_cspoly(
    data, xvalues, *, ax, width, alpha, faceup, facedn, edgeup, edgedn, wickup, wickdn,
    faceoff=None, use_prev_close=False, label=None
):
    """plots candlesticks — body rectangles + wick lines, final colors per up/dn

    Two criteria can be in play. The fill flag (hollow vs filled body) is
    always intrabar (close vs open). The up/dn color flag is intrabar by
    default, or interbar (close vs previous close) with
    ``use_prev_close=True`` — the first bar counts as up.

    ``faceoff`` is the third face color: the body fill for hollow
    (intrabar-up) bodies; ``None`` means bodies are always filled with the
    up/dn face colors.
    """

    high   = col_to_numpy(data, "high")
    low    = col_to_numpy(data, "low")
    open_  = col_to_numpy(data, "open")
    close  = col_to_numpy(data, "close")

    body_up = close >= open_  # fill criterion: always intrabar

    if use_prev_close:
        prev = np.concatenate((close[:1], close[:-1]))  # first bar compares to itself
        up = close >= prev
    else:
        up = body_up

    bottom = np.minimum(open_, close)
    top    = np.maximum(open_, close)

    # floats up front (datetime64 → date numbers) so spacing and verts share one scale
    xvalues = xvalues_to_float(xvalues)

    count = len(xvalues)

    if count > 0:
        spacing = np.nanmin(np.diff(xvalues)) if count > 1 else 1.0
    else:
        spacing = 1.0

    half_bar = spacing * width / 2.0

    edgecolor = np.where(up, edgeup, edgedn)
    wickcolor = np.where(up, wickup, wickdn)

    facecolor = np.where(up, faceup, facedn)
    if faceoff is not None:
        facecolor = np.where(body_up, faceoff, facecolor)

    linewidths = (0.7,)

    # wicks: two segments per bar (top → high, bottom → low), drawn beneath the bodies
    xv = xvalues
    wx = np.repeat(xv, 2)
    y0 = np.column_stack([top, bottom]).ravel()
    y1 = np.column_stack([high, low]).ravel()
    segments = np.stack([np.stack([wx, y0], axis=1), np.stack([wx, y1], axis=1)], axis=1)

    wicks = LineCollection(
        segments,  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # stubs say Sequence[ArrayLike]; 3-D ndarray is supported
        colors=np.repeat(wickcolor, 2),
        linewidths=linewidths,
        alpha=alpha,
    )

    # bodies: (n, 4, 2) rectangle vertex array — hits PolyCollection's set_verts fast path
    xl, xr = xv - half_bar, xv + half_bar
    kx = np.stack([xl, xl, xr, xr], axis=1)
    ky = np.stack([bottom, top, top, bottom], axis=1)
    verts = np.stack([kx, ky], axis=2)

    poly = PolyCollection(
        verts,  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # stubs say Sequence[ArrayLike]; 3-D ndarray is supported
        alpha=alpha,
        facecolors=facecolor,
        edgecolors=edgecolor,
        linewidths=linewidths,
        label=label,
    )

    ax.add_collection(wicks)
    ax.add_collection(poly)
    ax.autoscale_view()
