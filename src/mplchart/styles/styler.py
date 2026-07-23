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
import matplotlib.style

from ..colors import closest_color, normalize_color
from ..utils import extract_prefix


class _NoAxes:
    """Sentinel key for axis-less color cycles — weak-referenceable, unlike None."""


# mplchart's default look, as rc — the baseline layer under every styler:
# mpl defaults < DEFAULT_RC < stylesheet < rcparams overrides. Canvas pane
# config reads the effective rc instead of hardcoding these.
DEFAULT_RC: dict = {"axes.grid": True, "grid.alpha": 0.4}


def load_stylesheet(spec):
    """Load an rc mapping from a matplotlib stylesheet.

    Accepts what ``plt.style.use`` accepts: a stock style name
    (``matplotlib.style.library``), a path to an ``.mplstyle`` file, or the
    special name ``"default"`` — the factory-default template (minus
    non-style keys), giving an ambient-independent base. Named sheets and
    files return only the keys they define, so scoped application doesn't
    stomp the ambient theme. Values are validated by matplotlib's per-key
    validators, failing fast on garbage.
    """
    if spec == "default":
        # matplotlib special-cases this name in style.use the same way
        blacklist = mpl.style.core.STYLE_BLACKLIST  # ty: ignore[unresolved-attribute]  # pyright: ignore[reportAttributeAccessIssue]  # runtime attr, missing from stubs
        return {k: v for k, v in mpl.rcParamsDefault.items() if k not in blacklist}
    if isinstance(spec, str) and spec in mpl.style.library:
        return dict(mpl.style.library[spec])
    return dict(mpl.rc_params_from_file(spec, use_default_template=False))


def map_color_scheme(scheme):
    """Normalize a legacy ``color_scheme`` mapping into settings keys.

    Bare role keys get the color facet appended (``"macd"`` →
    ``"macd.color"``); keys already ending in ``".color"`` pass through.
    Transitional — retires with the ``color_scheme`` argument.
    """
    return {
        key if key.endswith(".color") else f"{key}.color": value
        for key, value in dict(scheme).items()
    }


def get_styler(style=None, *, overrides=(), color_scheme=()):
    """Normalize a style spec into a Styler.

    Args:
        style: ``None`` for an empty styler, or a prebuilt ``Styler``
            (passed through). Style specs (name, dict, ``Style``) will be
            accepted here when the Style spec lands.
        overrides: settings mapping (canonical dotted keys, e.g.
            ``candle.up.color``) layered on top of the style settings —
            whatever their source, a prebuilt Styler included.
        color_scheme: legacy color mapping (the ``color_scheme`` argument
            of Canvas/Chart), normalized via ``map_color_scheme`` and
            layered below ``overrides``. Retires with ``color_scheme``.
    """

    if isinstance(style, Styler):
        styler = style
    elif style is None:
        styler = Styler()
    elif isinstance(style, str):
        raise NotImplementedError("Style spec names not yet supported")  
    else:
        raise ValueError(f"Invalid style spec {style!r}")


    overrides = map_color_scheme(color_scheme) | dict(overrides)

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

    def get_setting(self, role, facet, *, fallback=None):
        """Lookup a setting by role and facet.

        The key is assembled as ``f"{role}.{facet}"`` and tried raw first,
        then with the role's extracted prefix (``"macd-12-26-9"`` →
        ``"macd"``); the facet never goes through prefix extraction.
        Defers to ``fallback`` on missing or ``None`` values only — falsy
        values like ``0.0`` are returned as-is.
        """
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
        color = override if override is not None else self.get_setting(role, "color", fallback=fallback)

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
