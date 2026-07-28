"""Style machinery — the runtime Styler.

The Styler holds all mutable styling state for one canvas: the settings
mapping, the alias map, the per-pane cycle counters, and the rc overrides
applied around artist creation.

Lookup vocabulary (see notes/styler-aliases.md) — five terms, one step each::

    name "SMA(20)" → prefix "sma" → alias → prefix "overlay" → key "overlay.color"

``name`` is what the caller passes (an indicator label or an already
canonical prefix), ``prefix`` is ``extract_prefix(name)`` (dots do not
split, so a prefix may carry a variant: ``candle.up``), the alias map is
the style-owned rename, ``facet`` is the trailing segment (``color``,
``alpha``), and ``key`` is what indexes ``settings`` — flat and dotted,
the rcParams shape, facet always explicit.

Symbolic color names are resolved eagerly to concrete colors here —
artists never see them, so no style state survives to draw time (see
notes/styler-sketch.md).
"""

from collections import Counter
from contextlib import contextmanager
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


def get_styler(style=None, *, overrides=()):
    """Normalize a style spec into a Styler.

    Args:
        style: ``None`` for the default ``"mplchart"`` style, a prebuilt
            ``Styler`` (passed through), or anything ``resolve_style``
            accepts — a shipped style name, a matplotlib stylesheet name,
            a spec mapping (``stylesheet``/``rc``/``settings``/``aliases``), or a
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
        styler = Styler(settings=spec.settings, rcparams=spec.rc, aliases=spec.aliases)
    else:
        spec = resolve_style(style)
        styler = Styler(settings=spec.settings, rcparams=spec.rc, aliases=spec.aliases)

    overrides = dict(overrides)

    if overrides:
        styler = styler.replace(overrides=overrides)

    return styler



class Styler:
    """Runtime styling state for one canvas.

    Args:
        settings (dict or iterable of pairs, optional): Mapping of flat
            dotted setting keys ``<prefix>.<facet>`` to values (e.g.
            ``candle.up.color``, ``volume.alpha``). Any value may be a list,
            which cycles per pane and key. A ``.color`` value may also be a
            ``"~"``-prefixed color (snapped to the closest prop-cycle
            color), or the ``"line"``/``"fill"`` sentinels (next color from
            the axes prop cycle).
        rcparams (dict or iterable of pairs, optional): matplotlib rcParams
            overrides, applied via ``context()`` around artist creation.
        stylesheet (str or Path, optional): base matplotlib stylesheet —
            what ``plt.style.use`` accepts: a stock style name or an
            ``.mplstyle`` path — loaded via ``load_stylesheet`` and
            collapsed eagerly under ``rcparams`` (explicit rcparams win).
            Every styler is totalized over the factory template
            (``base_template()``), so the stored rcparams are always fully
            specified — ambient rcParams never affect a chart.
        aliases (dict or iterable of pairs, optional): prefix renames
            applied during lookup — ``{"sma": "overlay", "ema": "overlay"}``
            makes every moving average draw from one ``overlay.color``
            cycle. A rename, not a fallback: the pre-alias prefix is never
            tried, which is what keys the shared cycle correctly.

    Cycle state lives in ``counters`` — a per-axes ``Counter`` of uses per
    key, created on first use and persisting for the lifetime of the styler
    (one chart) — fresh chart, fresh cycles. Axes are held weakly: when a
    pane is garbage-collected, its counters go with it.
    """

    def __init__(self, settings=(), rcparams=(), stylesheet=None, aliases=()):
        rc = load_stylesheet(stylesheet) if stylesheet else {}
        self.settings = dict(settings)
        self.aliases = dict(aliases)
        # totalized: factory template ⊕ sheet ⊕ explicit rc — every styler is
        # fully specified, ambient rcParams never leak into a chart
        self.rcparams = base_template() | rc | dict(rcparams)
        self.counters = WeakKeyDictionary()  # ax → Counter(key → uses)

    def replace(self, *, overrides=()):
        """Return a new Styler with ``overrides`` merged over the settings.

        Immutable-style (like ``dataclasses.replace``): always returns a new
        instance with fresh cycle state; ``self`` is untouched. rcparams and
        aliases carry over unchanged.
        """
        settings = self.settings | dict(overrides)
        return type(self)(settings=settings, rcparams=self.rcparams, aliases=self.aliases)

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

    def resolve_key(self, name, facet, *, extract=True):
        """Resolve a lookup key: name → prefix → alias → ``prefix.facet``.

        ``extract_prefix`` normalizes an indicator label to its prefix
        (``"SMA(50)"``/``"sma-50"`` → ``"sma"``) and leaves an already
        canonical prefix alone (``"candle.up"`` — dots do not split), so
        names from either source land on the same key; ``extract=False``
        skips it. The style's alias map then renames the prefix. The facet
        is never sanitized.
        """
        prefix = extract_prefix(name) if extract else name
        prefix = self.aliases.get(prefix, prefix)
        return f"{prefix}.{facet}"

    def next_value(self, values, key, ax):
        """Next entry of a cycled (list) setting value, by use count.

        Counts uses per ``(axes, key)`` and indexes modulo the list length,
        so the cycle wraps rather than running out — a two-color palette
        renders every overlay in one of two colors, whatever the count.
        Keyed per axes because a prebuilt Styler may be shared across
        charts; keyed per key (not per prefix) so ``overlay.color`` and
        ``overlay.alpha`` advance independently, staying in lockstep across
        instances rather than stealing each other's positions.
        """
        if ax is None:
            raise ValueError(
                f"Cycled (list) setting {key!r} needs axes to key its cycle on — "
                f"pass ax to get_setting/resolve_color"
            )

        counter = self.counters.setdefault(ax, Counter())
        index = counter[key]
        counter[key] += 1

        return values[index % len(values)]

    def get_setting(self, name, facet, ax=None, *, override=None, fallback=None, extract=True):
        """Lookup a setting by name and facet: override → setting → fallback.

        ``override`` (an explicit user value, e.g. a primitive kwarg) wins
        when not ``None``. Otherwise one lookup on the key resolved by
        ``resolve_key`` (name → prefix → alias → key), then ``fallback``.
        Each link defers on ``None`` only — falsy values like ``0.0`` or
        ``False`` are meaningful and returned as-is.

        A list setting value is a cycle: successive lookups of the same key
        on the same axes take successive entries, wrapping at the end (see
        ``next_value``). This is what makes an aliased group share one
        palette — ``sma``/``ema`` both resolving to ``overlay.color`` draw
        from one cursor. Cycling needs ``ax``; without it a list value
        raises. An empty list has nothing to cycle and defers to
        ``fallback``. Override and fallback values are used as given, never
        cycled.
        """
        if override is not None:
            return override

        if name is None:
            return fallback

        key = self.resolve_key(name, facet, extract=extract)
        value = self.settings.get(key)

        if isinstance(value, list):
            return self.next_value(value, key, ax) if value else fallback

        return fallback if value is None else value

    def resolve_color(self, name, ax=None, *, override=None, fallback=None, extract=True):
        """Resolve the color for a name: setting lookup, then color pipeline.

        The lookup — chain, aliasing and cycling — is ``get_setting(name,
        "color", ax)``; the name is a lookup key, never a color candidate.
        What is left here is color *interpretation* of the winner: ``"~"``
        snaps to the closest prop-cycle color, ``"line"``/``"fill"`` take
        the next color from the axes prop cycle (``None`` without axes).

        Returns a concrete hex string (or ``None``) — only hex leaves the
        styler: scalar-safe for ``np.where``, validated by ``to_rgba``.
        """
        color = self.get_setting(
            name, "color", ax, override=override, fallback=fallback, extract=extract
        )

        if isinstance(color, str):
            if color.startswith("~"):
                color = closest_color(color.removeprefix("~"))
            elif color == "line":
                color = self.next_line_color(ax) if ax is not None else None
            elif color == "fill":
                color = self.next_fill_color(ax) if ax is not None else None

        return normalize_color(color) if color is not None else None
