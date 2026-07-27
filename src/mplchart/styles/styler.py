"""Style machinery — the runtime Styler.

The Styler holds all mutable styling state for one canvas: the settings
mapping, the per-pane color cycles, and the rc overrides applied around
artist creation. Settings use flat dotted keys ``<role>[.<variant>].<facet>``
(e.g. ``candle.up.color``, ``volume.alpha``) — the rcParams shape, facet
always explicit. Symbolic color names are resolved eagerly to concrete
colors here — artists never see them, so no style state survives to draw
time (see notes/styler-sketch.md).
"""

from contextlib import contextmanager
from itertools import cycle
from weakref import WeakKeyDictionary

import matplotlib as mpl
import matplotlib.pyplot as plt

from ..colors import closest_color, normalize_color
from ..utils import extract_prefix
from .style import base_template, load_stylesheet, resolve_style


@contextmanager
def _scoped_rc(rcparams):
    """Apply ``rcparams`` scoped, restoring only those keys on exit."""
    saved = {key: mpl.rcParams[key] for key in rcparams}
    mpl.rcParams.update(rcparams)
    try:
        yield
    finally:
        mpl.rcParams.update(saved)


class _NoAxes:
    """Sentinel key for axis-less color cycles — weak-referenceable, unlike None."""


def get_styler(style=None, *, overrides=()):
    """Normalize a style spec into a Styler.

    Args:
        style: ``None`` for the default ``"mplchart"`` style, a prebuilt
            ``Styler`` (passed through), or anything ``resolve_style``
            accepts — a shipped style name, a matplotlib stylesheet name,
            a spec mapping (``stylesheet``/``rc``/``settings``), or a
            ``Style``. Every result is total: fully specified rc, no
            ambient inheritance.
        overrides: settings mapping (canonical dotted keys, e.g.
            ``candle.up.color``) layered on top of the style settings —
            whatever their source, a prebuilt Styler included.
    """

    if isinstance(style, Styler):
        styler = style
    elif style is None:
        spec = resolve_style("mplchart")   # the default style is a style
        styler = Styler(settings=spec.settings, rcparams=spec.rc)
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
            what ``plt.style.use`` accepts: a stock style name or an
            ``.mplstyle`` path — loaded via ``load_stylesheet`` and
            collapsed eagerly under ``rcparams`` (explicit rcparams win).
            Every styler is totalized over the factory template
            (``base_template()``), so the stored rcparams are always fully
            specified — ambient rcParams never affect a chart.

    Cycle state lives in ``cycles`` — a per-axes dict of per-role color
    cycles, created on first use and persisting for the lifetime of the
    styler (one chart) — fresh chart, fresh cycles. Axes are held weakly:
    when a pane is garbage-collected, its cycles go with it.
    """

    def __init__(self, settings=(), rcparams=(), stylesheet=None):
        rc = load_stylesheet(stylesheet) if stylesheet else {}
        self.settings = dict(settings)
        # totalized: factory template ⊕ sheet ⊕ explicit rc — every styler is
        # fully specified, ambient rcParams never leak into a chart
        self.rcparams = base_template() | rc | dict(rcparams)
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
        """Scoped, fully-specified rc — the style is the whole look.

        Restores only the keys it sets. A full-snapshot restore
        (``mpl.rc_context``) would also revert dynamic state such as
        ``interactive`` and ``backend``: when the chart is the first pyplot
        activity in a notebook kernel, the backend resolves *inside* this
        context, and reverting that on exit permanently disables inline
        auto-display (figures accumulate until an explicit ``show``).
        """
        return _scoped_rc(self.rcparams)

    def next_line_color(self, ax):
        """Next line color: text.color on an empty pane, then cycled colors.

        Emptiness is ``ax.has_data()`` — any data artist counts (labeled or
        not, whoever drew it); axis furniture (grid, ticks, spines) does not.
        A solitary line reads in the theme's ink; multiples differentiate
        via the prop cycle.
        """
        if ax.has_data():
            return ax._get_lines.get_next_color()
        else:
            return plt.rcParams["text.color"]

    def next_fill_color(self, ax):
        """Next cycled color for fill."""
        return ax._get_patches_for_fill.get_next_color()

    def get_setting(self, role, facet, *, override=None, fallback=None, extract=True):
        """Lookup a setting by role and facet: override → setting → fallback.

        ``override`` (an explicit user value, e.g. a primitive kwarg) wins
        when not ``None`` — the same chain as ``resolve_color``, minus the
        color pipeline. The role is sanitized to its canonical key via
        ``extract_prefix`` (``"SMA(50)"``/``"sma-50"`` → ``"sma"``) — a key
        is a key, not a label; pass ``extract=False`` when the role is
        already canonical. One lookup on ``f"{key}.{facet}"``; the facet is
        never sanitized. Each link defers on ``None`` only — falsy values
        like ``0.0`` or ``False`` are meaningful and returned as-is.
        """
        if override is not None:
            return override

        if role is None:
            return fallback

        key = extract_prefix(role) if extract else role
        value = self.settings.get(f"{key}.{facet}")

        return fallback if value is None else value

    def resolve_color(self, role, ax=None, *, override=None, fallback=None, extract=True):
        """Resolve the color for a role: chain, pipeline, then normalize.

        Chain: first non-None of ``override`` (explicit user color, e.g. a
        primitive kwarg) → the setting under the role's canonical key
        (sanitized via ``extract_prefix``: ``"SMA(50)"`` → ``"sma"``;
        ``extract=False`` skips) → ``fallback``. The role is a lookup key,
        never a color candidate.

        Pipeline on the winner: a list cycles per ``(axes, canonical key)``
        — per-instance labels share their role's cycle, so successive
        ``SMA(20)``/``SMA(50)`` take successive list colors; ``"~"`` snaps
        to the closest prop-cycle color; ``"line"``/``"fill"`` take the
        next color from the axes prop cycle (``None`` without axes).

        Returns a concrete hex string (or ``None``) — only hex leaves the
        styler: scalar-safe for ``np.where``, validated by ``to_rgba``.
        """
        key = extract_prefix(role) if (extract and role is not None) else role
        color = self.get_setting(key, "color", override=override, fallback=fallback, extract=False)

        if isinstance(color, list):
            if not color:
                color = None
            else:
                owner = ax if ax is not None else _NoAxes
                cycles = self.cycles.setdefault(owner, {})
                if key not in cycles:
                    cycles[key] = cycle(color)
                color = next(cycles[key])

        if isinstance(color, str):
            if color.startswith("~"):
                color = closest_color(color.removeprefix("~"))
            elif color == "line":
                color = self.next_line_color(ax) if ax is not None else None
            elif color == "fill":
                color = self.next_fill_color(ax) if ax is not None else None

        return normalize_color(color) if color is not None else None
