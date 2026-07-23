"""Style machinery — the runtime Styler.

The Styler holds all mutable styling state for one canvas: the settings
mapping, the per-pane color cycles, and the rc overrides applied around
artist creation. Settings use flat dotted keys ``<role>[.<variant>].<facet>``
(e.g. ``candle.up.color``, ``volume.alpha``) — the rcParams shape, facet
always explicit. Symbolic color names are resolved eagerly to concrete
colors here — artists never see them, so no style state survives to draw
time (see notes/styler-sketch.md).
"""

from itertools import cycle
from weakref import WeakKeyDictionary

import matplotlib as mpl
import matplotlib.pyplot as plt

from ..colors import closest_color, normalize_color
from ..utils import extract_prefix
from .style import load_stylesheet, resolve_style


class _NoAxes:
    """Sentinel key for axis-less color cycles — weak-referenceable, unlike None."""


# mplchart's default look, as rc — the baseline layer under every styler:
# mpl defaults < DEFAULT_RC < stylesheet < rcparams overrides. Canvas pane
# config reads the effective rc instead of hardcoding these.
DEFAULT_RC: dict = {"axes.grid": True, "grid.alpha": 0.4}


def get_styler(style=None, *, overrides=()):
    """Normalize a style spec into a Styler.

    Args:
        style: ``None`` for an empty styler, a prebuilt ``Styler`` (passed
            through), or anything ``resolve_style`` accepts — a shipped
            style name, a spec mapping (``stylesheet``/``rc``/``settings``),
            or a ``Style``.
        overrides: settings mapping (canonical dotted keys, e.g.
            ``candle.up.color``) layered on top of the style settings —
            whatever their source, a prebuilt Styler included.
    """

    if isinstance(style, Styler):
        styler = style
    elif style is None:
        styler = Styler()
    else:
        spec = resolve_style(style)
        styler = Styler(settings=spec.settings, rcparams=spec.rc)

    overrides = dict(overrides)

    if overrides:
        styler = styler.replace(overrides=overrides)

    return styler



class Styler:
    """Runtime styling state for one canvas.

    Args:
        settings (dict or iterable of pairs, optional): Mapping of flat
            dotted setting keys ``<role>[.<variant>].<facet>`` to values
            (e.g. ``candle.up.color``, ``volume.alpha``). A ``.color``
            value may be a color, a list of colors (cycled per pane and
            role), a ``"~"``-prefixed color (snapped to the closest
            prop-cycle color), or the ``"line"``/``"fill"`` sentinels
            (next color from the axes prop cycle).
        rcparams (dict or iterable of pairs, optional): matplotlib rcParams
            overrides, applied via ``context()`` around artist creation.
        stylesheet (str or Path, optional): base matplotlib stylesheet —
            what ``plt.style.use`` accepts: a stock style name, an
            ``.mplstyle`` path, or ``"default"`` (factory template,
            ambient-independent) — loaded via ``load_stylesheet`` and
            collapsed eagerly under ``rcparams`` (explicit rcparams win).
            Only the collapsed dict is stored; derived stylers carry it as
            plain rcparams.

    Cycle state lives in ``cycles`` — a per-axes dict of per-role color
    cycles, created on first use and persisting for the lifetime of the
    styler (one chart) — fresh chart, fresh cycles. Axes are held weakly:
    when a pane is garbage-collected, its cycles go with it.
    """

    def __init__(self, settings=(), rcparams=(), stylesheet=None):
        rc = load_stylesheet(stylesheet) if stylesheet else {}
        self.settings = dict(settings)
        self.rcparams = DEFAULT_RC | rc | dict(rcparams)  # later layers win
        self.cycles = WeakKeyDictionary()  # ax → {role: color iterator}

    def replace(self, *, overrides=()):
        """Return a new Styler with ``overrides`` merged over the settings.

        Immutable-style (like ``dataclasses.replace``): always returns a new
        instance with fresh cycle state; ``self`` is untouched. rcparams
        carry over unchanged.
        """
        settings = self.settings | dict(overrides)
        return type(self)(settings=settings, rcparams=self.rcparams)

    def context(self):
        """Scoped rc overrides — always at least the ``DEFAULT_RC`` baseline."""
        return mpl.rc_context(self.rcparams)

    def next_line_color(self, ax):
        """Next line color: text.color for the first trace, then cycled colors."""
        handles, _ = ax.get_legend_handles_labels()
        if len(handles):
            return ax._get_lines.get_next_color()
        else:
            return plt.rcParams["text.color"]

    def next_fill_color(self, ax):
        """Next cycled color for fill."""
        return ax._get_patches_for_fill.get_next_color()

    def get_setting(self, role, facet, *, override=None, fallback=None):
        """Lookup a setting by role and facet: override → setting → fallback.

        ``override`` (an explicit user value, e.g. a primitive kwarg) wins
        when not ``None`` — the same chain as ``resolve_color``, minus the
        color pipeline. The key is assembled as ``f"{role}.{facet}"`` and
        tried raw first, then with the role's extracted prefix
        (``"macd-12-26-9"`` → ``"macd"``); the facet never goes through
        prefix extraction. Each link defers on ``None`` only — falsy values
        like ``0.0`` or ``False`` are meaningful and returned as-is.
        """
        if override is not None:
            return override

        value = self.settings.get(f"{role}.{facet}")

        if value is None:
            prefix = extract_prefix(role)
            if prefix != role:
                value = self.settings.get(f"{prefix}.{facet}")

        return fallback if value is None else value

    def resolve_color(self, role, ax=None, *, override=None, fallback=None):
        """Resolve the color for a role: chain, pipeline, then normalize.

        Chain: first non-None of ``override`` (explicit user color, e.g. a
        primitive kwarg) → the ``role`` setting (raw, then extracted prefix —
        ``"macd-12-26-9"`` → ``"macd"``) → ``fallback``. The role is a lookup
        key, never a color candidate.

        Pipeline on the winner: a list cycles per ``(axes, role)`` as given
        (pass a stable role, not a per-instance label, to share a cycle);
        ``"~"`` snaps to the closest prop-cycle color; ``"line"``/``"fill"``
        take the next color from the axes prop cycle (``None`` without axes).

        Returns a concrete hex string (or ``None``) — only hex leaves the
        styler: scalar-safe for ``np.where``, validated by ``to_rgba``.
        """
        color = self.get_setting(role, "color", override=override, fallback=fallback)

        if isinstance(color, list):
            if not color:
                color = None
            else:
                owner = ax if ax is not None else _NoAxes
                cycles = self.cycles.setdefault(owner, {})
                if role not in cycles:
                    cycles[role] = cycle(color)
                color = next(cycles[role])

        if isinstance(color, str):
            if color.startswith("~"):
                color = closest_color(color.removeprefix("~"))
            elif color == "line":
                color = self.next_line_color(ax) if ax is not None else None
            elif color == "fill":
                color = self.next_fill_color(ax) if ax is not None else None

        return normalize_color(color) if color is not None else None
