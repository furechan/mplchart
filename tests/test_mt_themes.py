"""Tests for the morethemes theme loader (styles/morethemes.py)."""

import pytest
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

from mplchart.styles import Styler, get_styler
from mplchart.styles.morethemes import load_mt_style

morethemes = pytest.importorskip("morethemes")


@pytest.mark.parametrize("name", sorted(morethemes.ALL_THEMES))
def test_all_mt_themes_load(name):
    # rc validity is checked eagerly in the loader; Styler totalizes it
    styler = load_mt_style(name)
    assert isinstance(styler, Styler)
    assert styler.rcparams  # totalized without error


def test_economist_mapping():
    styler = load_mt_style("economist")
    assert styler.rcparams["axes.facecolor"] == "#e8f4f4"  # the theme's rc, complete look
    assert styler.settings == {}
    assert styler.aliases == {}


def test_unknown_theme_name():
    with pytest.raises(ValueError, match="Unknown morethemes theme"):
        load_mt_style("no-such-theme")


def test_mt_prefix_dispatch():
    from mplchart.styles import resolve_style

    styler = resolve_style("mt:economist")
    assert isinstance(styler, Styler)
    assert styler.rcparams == load_mt_style("economist").rcparams

    with pytest.raises(ValueError, match="Unknown morethemes theme"):
        resolve_style("mt:no-such-theme")


def test_prebuilt_styler_passthrough():
    styler = load_mt_style("economist")
    assert get_styler(styler) is styler


def test_chart_renders_with_mt_theme():
    from mplchart.chart import Chart
    from mplchart.primitives import Candlesticks, Volume
    from mplchart.samples import sample_prices

    styler = load_mt_style("economist")
    prices = sample_prices().tail(60)
    chart = Chart(prices, style=styler, figsize=(4, 3))
    try:
        chart.plot([Candlesticks(), Volume()])
        assert chart.figure.get_facecolor() == mcolors.to_rgba(styler.rcparams["figure.facecolor"])
    finally:
        plt.close("all")
