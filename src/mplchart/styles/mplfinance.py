"""mplfinance style interop — convert an mpf style into a ``Styler``.

``load_mpf_style`` takes a named mplfinance style (``"yahoo"``,
``"binance"``, ...) and returns the matching ``Styler``, usable anywhere
a style spec is accepted::

    from mplchart.styles.mplfinance import load_mpf_style

    chart = Chart(style=load_mpf_style("yahoo"))

The ``"mpf:"`` style prefix is the string form of the same conversion:
``Chart(style="mpf:yahoo")`` dispatches here via ``resolve_style``.

The rc half mirrors mplfinance's own ``_apply_mpfstyle`` semantics
(``base_mpl_style`` as the stylesheet, then ``rc``, then the face/grid
keys), except scoped and totalized like every mplchart style instead of
mutating global rcParams. ``marketcolors`` map onto the corresponding
settings keys, ``mavcolors`` becomes a shared ``overlay.color`` cycle
via aliases (the same model as the shipped ``cascade`` style), and
``y_on_right`` maps to the ``yaxis.right`` setting.

Requires `mplfinance <https://pypi.org/project/mplfinance/>`_, an optional
dependency of this module only, imported on call.
"""

from collections.abc import Mapping

import matplotlib as mpl
import matplotlib.style as mstyle

from .styler import Styler

# the moving-average prefixes folded onto the shared overlay cycle — what
# makes mavcolors cycle across indicators (see notes/styler-aliases.md)
MAV_ALIASES = {
    "sma": "overlay",
    "ema": "overlay",
    "wma": "overlay",
    "hma": "overlay",
    "rma": "overlay",
    "dema": "overlay",
    "tema": "overlay",
}


def _updown(entry):
    """Normalize a marketcolors entry to an ``(up, down)`` pair, or None.

    An entry may be a single color (both sides) or an up/down mapping.
    mplfinance's ``'inherit'`` sentinel (any prefix, e.g. ``'i'``) returns
    None — an unset key defers to mplchart's own fallback chain, which
    encodes the same inheritance (edges follow faces, wicks follow edges).
    """
    if entry is None:
        return None
    if isinstance(entry, Mapping):
        up, down = entry.get("up"), entry.get("down")
    else:
        up = down = entry
    for color in (up, down):
        if not isinstance(color, str) or "inherit".startswith(color):
            return None
    return up, down


def load_mpf_style(name):
    """Convert a named mplfinance style into a ``Styler``.

    Args:
        name: an mplfinance style name (``mpf.available_styles()``).

    Returns:
        The matching ``Styler`` — pass it to ``Chart(style=...)`` or layer
        it further via ``get_styler(..., overrides=...)``.
    """
    import mplfinance as mpf

    if name not in mpf.available_styles():
        available = ", ".join(mpf.available_styles())
        raise ValueError(f"Unknown mplfinance style {name!r} — available: {available}")

    style = mpf.make_mpf_style(base_mpf_style=name)

    sheet = style.get("base_mpl_style")
    if sheet == "seaborn-darkgrid" and "seaborn-v0_8-darkgrid" in mstyle.library:
        # mplfinance's own shim for the sheet matplotlib renamed
        sheet = "seaborn-v0_8-darkgrid"

    # rc assembly in _apply_mpfstyle order: rc first, then the dedicated
    # keys — including its unconditional axes.grid.axis reset — so the
    # converted look matches what mplfinance actually renders
    rc = dict(style.get("rc") or ())

    if style.get("facecolor") is not None:
        rc["axes.facecolor"] = style["facecolor"]
    if style.get("edgecolor") is not None:
        rc["axes.edgecolor"] = style["edgecolor"]
    if style.get("figcolor") is not None:
        rc["figure.facecolor"] = style["figcolor"]
        rc["savefig.facecolor"] = style["figcolor"]

    explicit_grid = False
    if style.get("gridcolor") is not None:
        explicit_grid = True
        rc["grid.color"] = style["gridcolor"]
    if style.get("gridstyle") is not None:
        explicit_grid = True
        rc["grid.linestyle"] = style["gridstyle"]

    rc["axes.grid.axis"] = "both"
    gridaxis = style.get("gridaxis")
    if gridaxis:
        explicit_grid = True
        if "horizontal".startswith(gridaxis):
            rc["axes.grid.axis"] = "y"
        elif "vertical".startswith(gridaxis):
            rc["axes.grid.axis"] = "x"

    if explicit_grid:
        rc["axes.grid"] = True

    marketcolors = style.get("marketcolors") or {}
    settings = {}

    if style.get("y_on_right") is not None:
        settings["yaxis.right"] = style["y_on_right"]

    pairs = {
        "candle": marketcolors.get("candle"),
        "edge": marketcolors.get("edge"),
        "wicks": marketcolors.get("wick"),
        "ohlc": marketcolors.get("ohlc"),
        "volume": marketcolors.get("volume"),
    }
    for prefix, entry in pairs.items():
        pair = _updown(entry)
        if pair:
            settings[f"{prefix}.up.color"], settings[f"{prefix}.down.color"] = pair

    # volume outlines: mpf never draws same-color edges — when vcedge equals
    # the faces it substitutes the faces darkened to 90% lightness
    # (its _adjust_color_brightness), which is volume.edge.lightness in
    # mplchart terms; a differing vcedge maps as declared colors
    vcedge = _updown(marketcolors.get("vcedge"))
    if vcedge:
        if vcedge == _updown(marketcolors.get("volume")):
            settings["volume.edge.lightness"] = 0.90
        else:
            settings["volume.edge.up.color"], settings["volume.edge.down.color"] = vcedge

    alpha = marketcolors.get("alpha")
    if alpha is not None and alpha != 1:
        # candle only — mpf applies marketcolors alpha to candle collections
        # (and hollow/renko variants) but never to ohlc bars
        settings["candle.alpha"] = alpha
    if marketcolors.get("volume_alpha") is not None:
        settings["volume.alpha"] = marketcolors["volume_alpha"]
    if marketcolors.get("vcdopcod"):
        settings["volume.use_prev_close"] = True
    if marketcolors.get("hollow") is not None:
        settings["candle.off.color"] = marketcolors["hollow"]

    aliases = {}
    mavcolors = style.get("mavcolors")
    if mavcolors:
        settings["overlay.color"] = list(mavcolors)
        aliases = dict(MAV_ALIASES)

    return Styler(
        settings=settings,
        rcparams=dict(mpl.RcParams(rc)),  # eager rc validation
        stylesheet=sheet,
        aliases=aliases,
    )
