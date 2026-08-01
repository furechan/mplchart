"""Matplotlib stylesheet layer — the rcParams side of the style machinery.

Everything here talks to matplotlib only: the factory template every styler
totalizes over (``base_template``) and stylesheet loading
(``load_stylesheet``). No mplchart style vocabulary — specs, settings,
aliases — lives at this layer.
"""

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
