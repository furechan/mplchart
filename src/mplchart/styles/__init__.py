"""Chart styling — static ``Style`` spec + runtime ``Styler``.

A chart's look is set with ``Chart(style=...)``, which accepts a shipped
style name (see ``available_styles``), a matplotlib stylesheet name, a spec
mapping (``stylesheet``/``rc``/``settings``), a ``Style``, or a prebuilt
``Styler``. Styles are total — ambient rcParams never affect the chart.

Design notes in ``notes/styler-sketch.md`` and ``notes/style-settings.md``.
"""

from .style import Style, available_styles, load_stylesheet, resolve_style
from .styler import Styler, get_styler

__all__ = [
    "Style",
    "Styler",
    "available_styles",
    "get_styler",
    "load_stylesheet",
    "resolve_style",
]
