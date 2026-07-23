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


def resolve_style(spec, *, name=""):
    """Normalize a style spec into a ``Style``.

    Accepted forms:
        - str: shipped style name — imports ``styles/lib/<name>.py`` and
          resolves its ``STYLE`` dict
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
            available = ", ".join(available_styles())
            raise ValueError(f"Unknown style {spec!r} — available: {available}") from None
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
