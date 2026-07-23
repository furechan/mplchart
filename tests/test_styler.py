"""Tests for the Styler runtime style machinery."""

import pytest
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from mplchart.styles import Styler, get_styler
from mplchart.styles.styler import DEFAULT_RC


class StubAxes:
    """Bare stand-in for axes as cycle keys (weak-referenceable, unlike object())."""


def hexc(color):
    """Expected resolve_color output: colors normalize to hex."""
    return mcolors.to_hex(color)


def test_scheme_lookup():
    styler = Styler(settings={"macd.color": "red", "sma.color": "blue"})
    assert styler.resolve_color("macd-12-26-9") == hexc("red")  # prefix match
    assert styler.resolve_color("sma") == hexc("blue")  # raw match
    assert styler.resolve_color("other", fallback="green") == hexc("green")
    assert styler.resolve_color("other") is None


def test_override_chain():
    styler = Styler(settings={"sma.color": "blue"})
    assert styler.resolve_color("sma", override="red") == hexc("red")  # override beats setting
    assert styler.resolve_color("sma", override="~red").startswith("#")  # pipeline applies
    rgb = (0.2, 0.65, 0.6)
    assert styler.resolve_color("sma", override=rgb) == hexc(rgb)  # munged to hex


def test_get_setting_facets():
    styler = Styler(settings={"candle.up.color": "green", "candle.alpha": 0.0})
    assert styler.get_setting("candle.up", "color") == "green"
    assert styler.get_setting("candle", "alpha", fallback=1.0) == 0.0  # falsy is meaningful
    assert styler.get_setting("candle", "width", fallback=0.8) == 0.8
    assert styler.get_setting("macd-12-26-9", "color", fallback="gray") == "gray"


def test_get_setting_prefix_chain():
    styler = Styler(settings={"sma.color": "blue"})
    assert styler.get_setting("sma-50", "color") == "blue"  # prefix on the name part only


def test_list_cycling_per_axes():
    styler = Styler(settings={"sma.color": ["red", "blue"]})
    ax1, ax2 = StubAxes(), StubAxes()
    assert styler.resolve_color("sma", ax1) == hexc("red")
    assert styler.resolve_color("sma", ax1) == hexc("blue")
    assert styler.resolve_color("sma", ax2) == hexc("red")  # independent cycle per pane
    assert styler.resolve_color("sma", ax1) == hexc("red")  # wraps around


def test_list_cycling_without_axes():
    styler = Styler(settings={"sma.color": ["red", "blue"]})
    assert styler.resolve_color("sma") == hexc("red")
    assert styler.resolve_color("sma") == hexc("blue")
    assert styler.resolve_color("sma") == hexc("red")  # axis-less cycles advance too


def test_cycles_die_with_axes():
    styler = Styler(settings={"sma.color": ["red", "blue"]})
    ax = StubAxes()
    styler.resolve_color("sma", ax)
    assert len(styler.cycles) == 1
    del ax
    assert len(styler.cycles) == 0  # weakly-keyed: pane gone, cycle gone


def test_non_string_colors_normalize():
    rgb = (0.2, 0.65, 0.6)
    styler = Styler(settings={"candle.up.color": rgb})
    assert styler.resolve_color("candle.up") == hexc(rgb)  # munged to hex, np.where-safe


def test_sentinels_without_axes_resolve_to_none():
    styler = Styler()
    assert styler.resolve_color("close", fallback="line") is None
    assert styler.resolve_color("volume", fallback="fill") is None


def test_closest_color_snapping():
    styler = Styler(settings={"sma.color": "~red"})
    color = styler.resolve_color("sma")
    assert color.startswith("#")  # snapped to a concrete prop-cycle color


def test_line_fill_sentinels():
    styler = Styler()
    fig, ax = plt.subplots()
    try:
        first = styler.resolve_color("close", ax, fallback="line")
        assert first == hexc(plt.rcParams["text.color"])  # first trace uses text.color
        ax.plot([0, 1], label="close")
        second = styler.resolve_color("sma", ax, fallback="line")
        assert second != first  # cycled color once labeled artists exist
        fill = styler.resolve_color("volume", ax, fallback="fill")
        assert fill
    finally:
        plt.close(fig)


def test_context_scoped_rc():
    styler = Styler(rcparams={"grid.color": "#123456"})
    before = plt.rcParams["grid.color"]
    with styler.context():
        assert plt.rcParams["grid.color"] == "#123456"
    assert plt.rcParams["grid.color"] == before


def test_get_styler_none():
    styler = get_styler(overrides={"candle.alpha": 0.9})
    assert isinstance(styler, Styler)
    assert styler.settings == {"candle.alpha": 0.9}  # canonical keys, no munging


def test_get_styler_passthrough():
    prebuilt = Styler(settings={"sma.color": "blue"})
    assert get_styler(prebuilt) is prebuilt


def test_get_styler_overrides_prebuilt():
    prebuilt = Styler(
        settings={"sma.color": "blue", "macd.color": "red"},
        rcparams={"grid.color": "#123456"},
    )
    styler = get_styler(prebuilt, overrides={"sma.color": "green"})
    assert styler is not prebuilt  # derived, prebuilt untouched
    assert styler.settings == {"sma.color": "green", "macd.color": "red"}
    assert styler.rcparams == DEFAULT_RC | {"grid.color": "#123456"}
    assert prebuilt.settings["sma.color"] == "blue"


def test_replace_immutable():
    styler = Styler(settings={"sma.color": "blue"}, rcparams={"grid.color": "#123456"})
    derived = styler.replace(overrides={"sma.color": "green", "candle.alpha": 0.9})
    assert derived is not styler
    assert derived.settings == {"sma.color": "green", "candle.alpha": 0.9}
    assert derived.rcparams == styler.rcparams
    assert styler.settings == {"sma.color": "blue"}  # untouched


def test_get_styler_invalid_spec():
    with pytest.raises(NotImplementedError):
        get_styler("nightclouds")  # style names arrive with the Style spec
    with pytest.raises(ValueError, match="Invalid style"):
        get_styler(42)


def test_canvas_accepts_prebuilt_styler():
    from mplchart.canvas import Canvas

    styler = Styler(settings={"sma.color": "blue"})
    canvas = Canvas(style=styler)
    try:
        assert canvas.styler is styler
        assert canvas.resolve_color("sma") == hexc("blue")
    finally:
        plt.close(canvas.figure)


def test_context_applies_baseline():
    # an empty styler carries exactly the DEFAULT_RC baseline, scoped
    styler = Styler()
    assert styler.rcparams == DEFAULT_RC
    before = dict(plt.rcParams)
    with styler.context():
        assert plt.rcParams["axes.grid"] is True
        assert plt.rcParams["grid.alpha"] == 0.4
    assert dict(plt.rcParams) == before  # fully restored outside


def test_load_stylesheet_library_name():
    from mplchart.styles import load_stylesheet

    rc = load_stylesheet("dark_background")
    assert mcolors.to_hex(rc["axes.facecolor"]) == "#000000"
    assert "figure.figsize" not in rc  # only the sheet's keys, not the template


def test_load_stylesheet_file(tmp_path):
    from mplchart.styles import load_stylesheet

    sheet = tmp_path / "custom.mplstyle"
    sheet.write_text("axes.facecolor: teal\ngrid.color: gray\n")
    rc = load_stylesheet(sheet)
    assert set(rc) == {"axes.facecolor", "grid.color"}
    assert mcolors.to_hex(rc["axes.facecolor"]) == mcolors.to_hex("teal")


def test_styler_stylesheet_composition():
    styler = Styler(stylesheet="dark_background", rcparams={"axes.facecolor": "navy"})
    assert styler.rcparams["axes.facecolor"] == "navy"  # explicit rc wins
    assert mcolors.to_hex(styler.rcparams["text.color"]) == "#ffffff"  # base carried

    derived = styler.replace(overrides={"sma.color": "red"})
    assert derived.rcparams == styler.rcparams  # collapsed rc carries over


def test_rc_context_wiring():
    from mplchart.canvas import Canvas

    canvas = Canvas(figsize=(2, 2), style=Styler(stylesheet="dark_background"))
    assert canvas.figure.get_facecolor() == mcolors.to_rgba("black")
    ax = canvas.get_axes("below")
    assert ax.get_facecolor() == mcolors.to_rgba("black")

    # ambient rc untouched outside the styler context
    assert plt.rcParams["figure.facecolor"] != "black"
    plt.close(canvas.figure)


def test_load_stylesheet_default():
    from mplchart.styles import load_stylesheet

    rc = load_stylesheet("default")
    assert rc["axes.facecolor"] == "white"
    assert "figure.figsize" in rc  # full template — ambient-independent base
    assert "backend" not in rc  # non-style keys filtered (STYLE_BLACKLIST)
