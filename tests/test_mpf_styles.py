"""Tests for the mplfinance style loader (styles/mplfinance.py)."""

import pytest
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

from mplchart.styles import Styler, get_styler
from mplchart.styles.mplfinance import load_mpf_style

mpf = pytest.importorskip("mplfinance")


@pytest.mark.parametrize("name", mpf.available_styles())
def test_all_mpf_styles_load(name):
    # rc validity is checked eagerly in the loader; Styler totalizes it
    styler = load_mpf_style(name)
    assert isinstance(styler, Styler)
    assert styler.rcparams["axes.grid.axis"] == "both"


def test_yahoo_mapping():
    styler = load_mpf_style("yahoo")
    assert styler.settings["candle.up.color"] == "#00b060"
    assert styler.settings["candle.down.color"] == "#fe3032"
    assert styler.settings["wicks.up.color"] == "#606060"
    assert styler.settings["volume.use_prev_close"] is True  # vcdopcod
    assert styler.settings["candle.alpha"] == 0.9
    assert styler.rcparams["axes.facecolor"] == "#fafafa"
    assert styler.rcparams["grid.color"] == "#d0d0d0"
    assert styler.rcparams["axes.grid"] is True
    # vcedge equals the volume faces — invisible outlines stay unmapped
    assert "volume.edge.up.color" not in styler.settings


def test_tradingview_volume_edges():
    styler = load_mpf_style("tradingview")
    assert styler.settings["volume.edge.up.color"] == "white"  # vcedge differs
    assert styler.settings["volume.alpha"] == 0.65  # volume_alpha


def test_nightclouds_mavcolors_cycle():
    styler = load_mpf_style("nightclouds")
    assert mcolors.to_hex(styler.rcparams["axes.facecolor"]) == "#0b0b0b"  # over dark_background
    assert styler.settings["overlay.color"][0] == "#40e0d0"
    assert styler.aliases["sma"] == styler.aliases["ema"] == "overlay"

    ax = plt.figure().add_subplot()
    try:
        drawn = [styler.resolve_color(name, ax) for name in ("SMA(20)", "EMA(50)")]
        assert drawn == [mcolors.to_hex(c) for c in styler.settings["overlay.color"][:2]]
    finally:
        plt.close("all")


def test_styles_without_mavcolors_declare_no_aliases():
    styler = load_mpf_style("yahoo")
    assert styler.aliases == {}
    assert "overlay.color" not in styler.settings


def test_make_mpf_style_dict():
    custom = mpf.make_mpf_style(base_mpf_style="charles", mavcolors=["red", "blue"])
    styler = load_mpf_style(custom)
    assert styler.settings["overlay.color"] == ["red", "blue"]
    assert styler.settings["candle.up.color"] == custom["marketcolors"]["candle"]["up"]


def test_unknown_style_name():
    with pytest.raises(ValueError, match="Unknown mplfinance style"):
        load_mpf_style("no-such-style")
    with pytest.raises(ValueError, match="Invalid mplfinance style"):
        load_mpf_style(42)


def test_mpf_prefix_dispatch():
    from mplchart.styles import resolve_style

    styler = resolve_style("mpf:yahoo")
    assert isinstance(styler, Styler)
    assert styler.settings == load_mpf_style("yahoo").settings

    with pytest.raises(ValueError, match="Unknown mplfinance style"):
        resolve_style("mpf:no-such-style")


def test_prebuilt_styler_passthrough():
    styler = load_mpf_style("yahoo")
    assert get_styler(styler) is styler


def test_chart_renders_with_mpf_style():
    from mplchart.chart import Chart
    from mplchart.primitives import Candlesticks, Volume
    from mplchart.samples import sample_prices

    styler = load_mpf_style("binancedark")
    prices = sample_prices().tail(60)
    chart = Chart(prices, style=styler, figsize=(4, 3))
    try:
        chart.plot([Candlesticks(), Volume()])
        assert chart.figure.get_facecolor() == mcolors.to_rgba(styler.rcparams["figure.facecolor"])
    finally:
        plt.close("all")
