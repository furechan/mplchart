"""Tests for style resolution and the shipped styles."""

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from mplchart.styles import Styler, available_styles, get_styler, resolve_style
from mplchart.styles.stylesheet import STYLE_BLACKLIST, base_template


def test_available_styles():
    names = available_styles()
    assert {"cascade", "chartist", "modern", "mplchart", "nightclouds"} <= set(names)


def test_resolve_style_name():
    styler = resolve_style("nightclouds")
    assert mcolors.to_hex(styler.rcparams["axes.facecolor"]) == "#000000"  # base sheet collapsed
    assert styler.rcparams["grid.color"] == "#333333"  # explicit rc wins over the sheet
    assert styler.settings["candle.up.color"] == "white"


def test_get_styler_mapping():
    styler = get_styler({
        "stylesheet": "dark_background",
        "rc": {"grid.color": "red"},
        "settings": {"sma.color": "blue"},
    })
    assert styler.rcparams["grid.color"] == "red"
    assert mcolors.to_hex(styler.rcparams["text.color"]) == "#ffffff"
    assert styler.settings == {"sma.color": "blue"}


def test_style_blacklist_resolves():
    """Whichever spelling this matplotlib uses, the set must be usable.

    Private since 3.11 (``style._STYLE_BLACKLIST``), public before it
    (``style.core.STYLE_BLACKLIST``) — a rename on either side would surface
    here, as an ImportError at import or as a set that lost its contents.
    """
    assert {"backend", "interactive"} <= set(STYLE_BLACKLIST)


def test_base_template_excludes_non_style_keys():
    template = base_template()
    assert not (set(template) & set(STYLE_BLACKLIST))  # backend, interactive, ...
    assert "figure.dpi" not in template  # environment preference, not a look
    assert "axes.grid" in template  # a real style key survives


def test_get_styler_aliases():
    styler = get_styler({
        "settings": {"overlay.color": ["red", "blue"]},
        "aliases": {"sma": "overlay"},
    })
    assert styler.aliases == {"sma": "overlay"}
    assert get_styler(styler).aliases == {"sma": "overlay"}  # passthrough keeps them


def test_styles_without_aliases_declare_none():
    # no library-wide default map — aliases ship with the style that wants them
    assert resolve_style("nightclouds").aliases == {}
    assert resolve_style("dark_background").aliases == {}  # a plain mpl sheet
    assert get_styler({"rc": {"grid.color": "red"}}).aliases == {}


def test_cascade_shares_one_overlay_cycle():
    styler = get_styler("cascade")
    palette = styler.settings["overlay.color"]
    assert styler.aliases["sma"] == styler.aliases["ema"] == "overlay"

    ax = plt.figure().add_subplot()
    try:
        drawn = [styler.resolve_color(name, ax) for name in ("SMA(20)", "EMA(50)", "sma-200")]
        assert drawn == [mcolors.to_hex(c) for c in palette[:3]]  # one cursor, in order
    finally:
        plt.close("all")


def test_get_styler_resolves_specs():
    styler = get_styler("nightclouds")
    assert isinstance(styler, Styler)
    assert styler.settings["candle.up.color"] == "white"
    assert styler.rcparams["grid.color"] == "#333333"

    styler = get_styler({"settings": {"sma.color": "blue"}})
    assert styler.settings == {"sma.color": "blue"}


def test_canvas_style_by_name():
    from mplchart.canvas import Canvas

    canvas = Canvas(figsize=(2, 2), style="nightclouds")
    try:
        assert canvas.figure.get_facecolor() == mcolors.to_rgba("black")
    finally:
        plt.close(canvas.figure)


def test_standard_sheet_as_style():
    # matplotlib sheet names are accepted as whole looks — no mplchart opinions
    styler = resolve_style("ggplot")
    assert styler.rcparams["axes.grid"] is True  # ggplot's own grid, full alpha

    from mplchart.canvas import Canvas

    canvas = Canvas(figsize=(2, 2), style="classic")  # classic sheet: gridless
    root = canvas.root_axes()
    assert not root.xaxis.get_gridlines()[0].get_visible()
    plt.close(canvas.figure)


def test_styles_are_ambient_isolated():
    # totalized styles: ambient rcParams never affect a chart
    from mplchart.canvas import Canvas
    import matplotlib.colors as mc

    with plt.rc_context({"axes.facecolor": "black", "axes.grid": False}):
        canvas = Canvas(figsize=(2, 2))  # default mplchart style
        root = canvas.root_axes()
        assert root.get_facecolor() == mc.to_rgba("white")  # template, not ambient
        assert root.xaxis.get_gridlines()[0].get_visible()
        plt.close(canvas.figure)


def test_provider_packages_have_zero_blast_radius():
    # mplfinance/morethemes are imported only inside their loader functions —
    # with both blocked, the whole package imports and charts render; only
    # the loader calls may raise. A new top-level provider import fails here.
    import subprocess
    import sys

    script = """
import sys

class Block:
    BLOCKED = {"morethemes", "mplfinance"}
    def find_module(self, name, path=None):
        if name.split(".")[0] in self.BLOCKED:
            return self
    def load_module(self, name):
        raise ImportError(f"blocked: {name}")

sys.meta_path.insert(0, Block())

import matplotlib
matplotlib.use("Agg")

import mplchart.styles.mplfinance
import mplchart.styles.morethemes
from mplchart.chart import Chart
from mplchart.primitives import Candlesticks
from mplchart.samples import sample_prices
from mplchart.styles import get_styler, resolve_style

resolve_style("cascade")
get_styler(None)
Chart(sample_prices().tail(30), figsize=(3, 2)).plot([Candlesticks()])

for load, name in [
    (mplchart.styles.mplfinance.load_mpf_style, "yahoo"),
    (mplchart.styles.morethemes.load_mt_theme, "economist"),
    (get_styler, "mpf:yahoo"),
    (get_styler, "mt:economist"),
]:
    try:
        load(name)
    except ImportError:
        pass
    else:
        raise AssertionError(f"{load.__name__}({name!r}) did not raise with provider blocked")
"""
    subprocess.run([sys.executable, "-c", script], check=True)


def test_style_namespaces_are_disjoint():
    # the style name chain (lib → mpl sheets) shares one flat namespace —
    # this tripwire turns silent shadowing into a loud failure the moment
    # either registry grows an overlapping name (external providers resolve
    # via explicit loaders, outside this namespace)
    import matplotlib.style

    lib = set(available_styles())
    sheets = set(matplotlib.style.library) | {"default"}
    assert not lib & sheets, f"lib styles shadow matplotlib sheets: {lib & sheets}"
