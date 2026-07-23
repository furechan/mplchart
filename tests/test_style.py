"""Tests for the static Style spec, resolve_style, and shipped styles."""

import pytest
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from mplchart.styles import Style, Styler, available_styles, get_styler, resolve_style


def test_available_styles():
    names = available_styles()
    assert {"nightclouds", "stockcharts", "tradingview"} <= set(names)


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
