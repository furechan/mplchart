"""Style name registries — what ``resolve_style`` consults.

Shipped styles live as zero-import ``STYLE`` dict modules under
``styles/lib/`` — the directory is the registry, adding a style is one new
file (see notes/styler-sketch.md). Provider prefixes map install-dependent
namespaces to their loader modules.
"""

from pkgutil import iter_modules

# provider prefixes — "mpf:yahoo" dispatches to the matching loader module,
# imported lazily so the provider packages keep zero blast radius. Prefixes
# keep install-dependent names out of the flat lib/sheet namespace (mpf's
# nightclouds/classic/default collide outright).
ENTRY_POINTS = {
    "mpf": ("mplfinance", "load_mpf_style"),
    "mt": ("morethemes", "load_mt_theme"),
}


def available_styles():
    """Names of the shipped styles — ``styles/lib/`` is the registry."""
    from . import lib

    return sorted(module.name for module in iter_modules(lib.__path__))
