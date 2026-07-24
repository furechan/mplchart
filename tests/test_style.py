"""Tests for the static Style spec, resolve_style, and shipped styles."""

import pytest
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from mplchart.styles import Style, Styler, available_styles, get_styler, resolve_style


def test_available_styles():
    names = available_styles()
    assert {"chartist", "modern", "mplchart", "nightclouds"} <= set(names)


def test_resolve_style_name():
    style = resolve_style("nightclouds")
    assert style.name == "nightclouds"
    assert mcolors.to_hex(style.rc["axes.facecolor"]) == "#000000"  # base sheet collapsed
    assert style.rc["grid.color"] == "#333333"  # explicit rc wins over the sheet
    assert style.settings["candle.up.color"] == "white"


def test_resolve_style_mapping():
    style = resolve_style({
        "stylesheet": "dark_background",
        "rc": {"grid.color": "red"},
        "settings": {"sma.color": "blue"},
    })
    assert style.rc["grid.color"] == "red"
    assert mcolors.to_hex(style.rc["text.color"]) == "#ffffff"
    assert style.settings == {"sma.color": "blue"}


def test_resolve_style_passthrough():
    style = Style(rc={"grid.color": "red"})
    assert resolve_style(style) is style


def test_style_validates_rc():
    # matplotlib's per-key validators are the schema — errors at definition
    with pytest.raises(ValueError):
        Style(rc={"grid.color": "no-such-color"})
    with pytest.raises(KeyError):
        Style(rc={"no.such.key": 1})


def test_unknown_style_name():
    with pytest.raises(ValueError, match="Unknown style"):
        resolve_style("no-such-style")


def test_unknown_spec_keys():
    with pytest.raises(ValueError, match="Unknown style keys"):
        resolve_style({"colors": {}})


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
    style = resolve_style("ggplot")
    assert style.name == "ggplot"
    assert style.rc["axes.grid"] is True  # ggplot's own grid, full alpha

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
