"""Style name registries — what ``resolve_style`` consults.

Shipped styles live as zero-import ``STYLE`` dict modules under
``styles/lib/`` — the directory is the registry, adding a style is one new
file (see notes/styler-sketch.md). Provider prefixes map install-dependent
namespaces to their loader modules.
"""

from importlib.metadata import entry_points
from pkgutil import iter_modules


def style_handler(prefix):
    """Loader for a provider ``prefix`` — resolved from the
    ``mplchart.styles`` entry-point group (declared in pyproject.toml),
    imported lazily on load. Any installed package can register a prefix
    by declaring an entry in the same group.
    """
    eps = entry_points(group="mplchart.styles")
    if prefix not in eps.names:
        known = ", ".join(sorted(eps.names))
        raise ValueError(f"Unknown style prefix {prefix!r} — known prefixes: {known}")
    return eps[prefix].load()

def available_styles():
    """Names of the shipped styles — ``styles/lib/`` is the registry."""
    from . import lib

    return sorted(module.name for module in iter_modules(lib.__path__))
