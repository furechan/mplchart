"""Chart styling — the runtime ``Styler`` and its spec forms.

A chart's look is set with ``Chart(style=...)``, which accepts a shipped
style name (see ``available_styles``), a matplotlib stylesheet name, a
provider-prefixed name (``"mpf:yahoo"`` for mplfinance styles,
``"mt:economist"`` for morethemes — requires that provider package), a spec
mapping (``stylesheet``/``rc``/``settings``/``aliases``), or a prebuilt
``Styler``. Styles are total — ambient rcParams never affect the chart.

Design notes in ``notes/styler-sketch.md``, ``notes/styler-settings.md`` and
``notes/styler-aliases.md``.
"""

from .registry import available_styles
from .styler import Styler, get_styler, resolve_style
from .stylesheet import load_stylesheet

__all__ = [
    "Styler",
    "available_styles",
    "get_styler",
    "load_stylesheet",
    "resolve_style",
]
