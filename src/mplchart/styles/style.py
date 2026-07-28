"""Style spec — the static half of the style machinery.

``Style`` is a frozen spec (validated rc overrides + symbolic settings);
``resolve_style`` normalizes any style spec form — shipped style name,
mapping, or ``Style`` — into one. Shipped styles live as zero-import
``STYLE`` dict modules under ``styles/lib/``: the directory is the
registry, adding a style is one new file (see notes/styler-sketch.md).
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from importlib import import_module
from pkgutil import iter_modules

import matplotlib as mpl
import matplotlib.style

# the keys matplotlib refuses to let a style set — private since 3.11, where the
# ``style.core`` module became a deprecated shim due for removal in 3.13.
# New name first: importing ``core`` on 3.11+ succeeds and warns, so trying it
# first would keep emitting that deprecation until the module disappears.
try:
    from matplotlib.style import _STYLE_BLACKLIST as STYLE_BLACKLIST  # matplotlib >= 3.11  # ty: ignore[unresolved-import]  # pyright: ignore[reportAttributeAccessIssue]  # private, missing from stubs
except ImportError:
    from matplotlib.style.core import STYLE_BLACKLIST  # matplotlib <= 3.10  # ty: ignore[unresolved-import]  # pyright: ignore[reportAttributeAccessIssue]  # runtime attr, missing from stubs


# rcParams the totalized base never touches: matplotlib's own non-style keys
# (backend, interactive, ...) plus environment preferences that belong to the
# user's session, not to a look (dpi overrides survive styling).
ENVIRONMENT_KEYS = frozenset({"figure.dpi", "savefig.dpi"})


def base_template():
    """The factory rcParams template minus non-style and environment keys.

    Every Styler is totalized over this base — charts are fully specified
    and render identically regardless of ambient rcParams (no ambient
    inheritance; scoped, unlike mplfinance's global reset).
    """
    return {
        k: v for k, v in mpl.rcParamsDefault.items()
        if k not in STYLE_BLACKLIST and k not in ENVIRONMENT_KEYS
    }


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
        return base_template()
    if isinstance(spec, str) and spec in mpl.style.library:
        return dict(mpl.style.library[spec])
    return dict(mpl.rc_params_from_file(spec, use_default_template=False))


@dataclass(frozen=True)
class Style:
    """Static style spec: validated rc overrides + symbolic settings.

    Args:
        name: display name (the module name for shipped styles).
        rc: matplotlib rcParams overrides — validated eagerly by
            round-tripping through ``mpl.RcParams``, so a bad key or value
            errors at the style definition, not the first plot.
        settings: flat dotted settings keys (``candle.up.color``, ...).
    """

    name: str = ""
    rc: dict = field(default_factory=dict)
    settings: dict = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "rc", dict(mpl.RcParams(self.rc)))
        object.__setattr__(self, "settings", dict(self.settings))


def external_theme_rc(name):
    """rc dict for ``name`` from optional external theme packages, or None.

    Currently supports `morethemes <https://pypi.org/project/morethemes/>`_
    when installed: its themes resolve as complete looks
    (``style="economist"``), after lib styles and matplotlib sheets.
    """
    try:
        import morethemes
    except ImportError:
        return None

    if name in getattr(morethemes, "ALL_THEMES", {}):
        return dict(morethemes.get_rcparams(name))

    return None


def resolve_style(spec, *, name=""):
    """Normalize a style spec into a ``Style``.

    Accepted forms:
        - str: shipped style name (``styles/lib/<name>.py``, which shadows),
          a matplotlib stylesheet name, or a theme from an installed
          provider package (morethemes) — sheets and external themes are
          the complete look, no mplchart opinions
        - mapping: ``{"stylesheet": ..., "rc": ..., "settings": ...}`` (all
          optional) — the stylesheet (anything ``load_stylesheet`` accepts)
          is collapsed eagerly under the explicit rc
        - Style: passthrough
    """
    if isinstance(spec, Style):
        return spec

    if isinstance(spec, str):
        try:
            module = import_module(f".lib.{spec}", __package__)
        except ModuleNotFoundError:
            if spec == "default" or spec in mpl.style.library:
                # a standard matplotlib stylesheet as the whole look —
                # no mplchart opinions ride along (grid keys per the sheet)
                return resolve_style({"stylesheet": spec}, name=spec)
            rc = external_theme_rc(spec)
            if rc is not None:
                # an external theme as the whole look (e.g. morethemes)
                return resolve_style({"rc": rc}, name=spec)
            available = ", ".join(available_styles())
            raise ValueError(
                f"Unknown style {spec!r} — available: {available}, "
                f"any matplotlib stylesheet name, or a theme from an "
                f"installed provider (morethemes)"
            ) from None
        return resolve_style(module.STYLE, name=spec)

    if isinstance(spec, Mapping):
        spec = dict(spec)
        name = spec.pop("name", name)
        sheet = spec.pop("stylesheet", None)
        rc = load_stylesheet(sheet) if sheet else {}
        rc |= dict(spec.pop("rc", ()) or ())
        settings = dict(spec.pop("settings", ()) or ())
        if spec:
            raise ValueError(f"Unknown style keys: {sorted(spec)}")
        return Style(name=name, rc=rc, settings=settings)

    raise ValueError(f"Invalid style spec {spec!r}")


def available_styles():
    """Names of the shipped styles — ``styles/lib/`` is the registry."""
    from . import lib

    return sorted(module.name for module in iter_modules(lib.__path__))
