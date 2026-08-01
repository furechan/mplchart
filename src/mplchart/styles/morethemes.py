"""morethemes interop — convert a morethemes theme into a ``Styler``.

``load_mt_theme`` takes a named morethemes theme (``"economist"``,
``"wsj"``, ...) and returns the matching ``Styler``, usable anywhere a
style spec is accepted::

    from mplchart.styles.morethemes import load_mt_theme

    chart = Chart(style=load_mt_theme("economist"))

The ``"mt:"`` style prefix is the string form of the same conversion:
``Chart(style="mt:economist")`` dispatches here via ``resolve_style``.

The theme is the complete look — its rcParams, no mplchart opinions —
scoped and totalized like every mplchart style instead of set globally
via ``morethemes.set_theme``.

Requires `morethemes <https://pypi.org/project/morethemes/>`_, an optional
dependency of this module only, imported on call.
"""

import matplotlib as mpl

from .styler import Styler


def load_mt_theme(name):
    """Convert a morethemes theme into a ``Styler``.

    Args:
        name: a morethemes theme name (``morethemes.ALL_THEMES``).

    Returns:
        The matching ``Styler`` — pass it to ``Chart(style=...)`` or layer
        it further via ``get_styler(..., overrides=...)``.
    """
    import morethemes

    if name not in morethemes.ALL_THEMES:
        available = ", ".join(morethemes.ALL_THEMES)
        raise ValueError(f"Unknown morethemes theme {name!r} — available: {available}")

    rc = dict(mpl.RcParams(morethemes.get_rcparams(name)))  # eager rc validation
    return Styler(rcparams=rc)
