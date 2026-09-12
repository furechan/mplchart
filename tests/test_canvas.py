"""Tests for the Canvas presentation plane."""

import pytest
import matplotlib.pyplot as plt

from mplchart.canvas import Canvas


@pytest.fixture
def canvas():
    canvas = Canvas()
    yield canvas
    plt.close(canvas.figure)


def test_canvas_creates_styled_root_and_main(canvas):
    assert len(canvas.figure.axes) == 2
    root = canvas.root_axes()
    assert root._label == "root"
    assert root.get_xmargin() == 0.0
    assert canvas.count_axes() == 1
    main = canvas.figure.axes[1]
    assert main.get_xmargin() == 0.0
    assert not main.patch.get_visible()


def test_canvas_title():
    canvas = Canvas(title="AAPL")
    assert canvas.root_axes().get_title() == "AAPL"
    canvas.set_title("MSFT")
    assert canvas.root_axes().get_title() == "MSFT"
    plt.close(canvas.figure)


def test_canvas_render(canvas):
    canvas.get_axes()
    result = canvas.render(format="svg")
    assert isinstance(result, bytes)
    assert b"<svg" in result


def test_canvas_render_metadata(canvas):
    result = canvas.render(format="svg", metadata={"Title": "AAPL chart"})
    assert b"<dc:title>AAPL chart</dc:title>" in result


def test_canvas_adopts_existing_figure():
    figure = plt.figure()
    figure.add_subplot()  # content to be cleared
    canvas = Canvas(figure=figure)
    assert canvas.figure is figure
    assert len(figure.axes) == 2  # cleared, root and main
    plt.close(figure)


def test_get_axes_selects_existing_main_pane(canvas):
    ax = canvas.figure.axes[1]
    assert canvas.get_axes() is ax
    assert canvas.count_axes() == 1
    assert canvas.main_axes() is ax
    assert canvas.get_axes("same") is ax
    assert canvas.get_axes("main") is ax


def test_new_axes_above_below(canvas):
    main = canvas.get_axes()
    below = canvas.new_axes("below")
    above = canvas.new_axes("above")
    assert canvas.count_axes() == 3
    assert len({id(main), id(below), id(above)}) == 3
    assert canvas.main_axes() is main
    assert canvas.get_axes("same") is above  # last created pane is current


def test_get_axes_rejects_creating_targets(canvas):
    # creation goes through new_axes (Pane) — get_axes is selective only
    with pytest.raises(ValueError, match="Invalid target"):
        canvas.get_axes("below")
    with pytest.raises(ValueError, match="Invalid target"):
        canvas.get_axes("above")


def test_new_axes_rejects_selecting_positions(canvas):
    with pytest.raises(ValueError, match="Invalid position"):
        canvas.new_axes("main")


def test_get_axes_twinx_empty_pane_is_itself(canvas):
    # an empty pane is its own overlay — nothing to be scale-independent from
    main = canvas.get_axes()
    assert canvas.get_axes("twinx") is main
    assert canvas.count_axes(include_twins=True) == 1


def test_get_axes_twinx(canvas):
    main = canvas.get_axes()
    main.plot([1.0, 2.0])  # content to overlay
    twin = canvas.get_axes("twinx")
    assert twin is not main
    assert twin._label == "twinx"
    assert canvas.count_axes() == 1
    assert canvas.count_axes(include_twins=True) == 2


def test_get_axes_invalid_target(canvas):
    with pytest.raises(ValueError, match="Invalid target"):
        canvas.get_axes("bogus")


def test_yaxis_default_right(canvas):
    # the default "mplchart" style declares yaxis.right True — the finance convention
    assert canvas.yaxis_right is True
    pane = canvas.get_axes()
    assert pane.yaxis.get_ticks_position() == "right"


def test_yaxis_sheet_style_left():
    # a style with no yaxis.right opinion keeps matplotlib's left convention
    from mplchart.styles import Styler

    canvas = Canvas(figsize=(2, 2), style=Styler(stylesheet="classic"))
    assert canvas.yaxis_right is False
    assert canvas.get_axes().yaxis.get_ticks_position() == "left"
    plt.close(canvas.figure)


def test_yaxis_right_setting():
    from mplchart.styles import get_styler

    style = get_styler("mplchart", overrides={"yaxis.right": False})
    canvas = Canvas(figsize=(2, 2), style=style)
    assert canvas.yaxis_right is False
    assert canvas.get_axes().yaxis.get_ticks_position() == "left"
    plt.close(canvas.figure)

    # the explicit param beats the setting
    canvas = Canvas(figsize=(2, 2), style=style, yaxis_right=True)
    assert canvas.yaxis_right is True
    plt.close(canvas.figure)


def test_yaxis_left():
    canvas = Canvas(figsize=(2, 2), yaxis_right=False)
    pane = canvas.get_axes()
    assert pane.yaxis.get_ticks_position() == "left"
    pane.plot([1.0, 2.0])
    twin = canvas.get_axes("twinx")  # twin overlay takes the opposite side
    assert twin.yaxis.get_ticks_position() == "right"
    plt.close(canvas.figure)


def test_yaxis_invalid():
    with pytest.raises(ValueError, match="Invalid yaxis_right"):
        Canvas(yaxis_right="left")


def test_yaxis_default_linear(canvas):
    assert canvas.yaxis_log is False
    assert canvas.main_axes().get_yscale() == "linear"


@pytest.mark.parametrize("yaxis_log", [False, True])
def test_yaxis_log_main_only(yaxis_log):
    canvas = Canvas(yaxis_log=yaxis_log)
    try:
        main = canvas.main_axes()
        main.plot([1.0, 10.0, 100.0])
        twin = canvas.get_axes("twinx")
        below = canvas.new_axes("below")
        above = canvas.new_axes("above")
        assert main.get_yscale() == ("log" if yaxis_log else "linear")
        for ax in (canvas.root_axes(), twin, below, above):
            assert ax.get_yscale() == "linear"
        assert b"<svg" in canvas.render()
    finally:
        plt.close(canvas.figure)


@pytest.mark.parametrize("value", [None, "log", 2])
def test_yaxis_log_invalid(value):
    with pytest.raises(ValueError, match="Invalid yaxis_log"):
        Canvas(yaxis_log=value)


def test_resolve_color_scheme_lookup():
    from matplotlib.colors import to_hex

    from mplchart.styles import Styler

    canvas = Canvas(style=Styler(settings={"macd.color": "red", "sma.color": "blue"}))
    assert canvas.resolve_color("macd-12-26-9") == to_hex("red")  # prefix match
    assert canvas.resolve_color("sma") == to_hex("blue")  # raw match
    assert canvas.resolve_color("other", fallback="green") == to_hex("green")
    plt.close(canvas.figure)


def test_resolve_color_list_cycling():
    from matplotlib.colors import to_hex

    from mplchart.styles import Styler

    canvas = Canvas(style=Styler(settings={"sma.color": ["red", "blue"]}))
    ax = canvas.get_axes()
    assert canvas.resolve_color("sma", ax=ax) == to_hex("red")
    assert canvas.resolve_color("sma", ax=ax) == to_hex("blue")
    assert canvas.resolve_color("sma", ax=ax) == to_hex("red")  # wraps around
    plt.close(canvas.figure)


def test_canvas_view_native_plot():
    """The canonical no-Chart usage: canvas + view + dateaxis, native plotting."""
    pytest.importorskip("pandas")
    from mplchart.dataview import get_view
    from mplchart.dateaxis import config_date_axis
    from mplchart.samples import sample_prices

    prices = sample_prices(freq="daily", backend="pandas")
    canvas = Canvas(figsize=(12, 9))
    view = get_view(prices, max_bars=100)
    config_date_axis(canvas.root_axes(), view.dates)

    ax = canvas.get_axes()
    ax.plot(*view.series_xy(view.eval("close")))
    below = canvas.new_axes("below")
    below.plot(*view.series_xy(view.eval(lambda p: p["close"].rolling(20).mean())))

    assert canvas.count_axes() == 2
    xs = ax.lines[0].get_xdata()
    assert len(xs) == 100
    plt.close(canvas.figure)


def test_grid_default_look():
    # the default "mplchart" style: root x-grid and pane y-grid on, alpha 0.4
    canvas = Canvas(figsize=(2, 2))
    root = canvas.root_axes()
    pane = canvas.new_axes("below")
    assert root.xaxis.get_gridlines()[0].get_visible()
    assert pane.yaxis.get_gridlines()[0].get_visible()
    assert root.xaxis.get_gridlines()[0].get_alpha() == 0.4
    plt.close(canvas.figure)


def test_grid_off_via_stylesheet():
    # the classic sheet sets axes.grid False — styles can disable the grid
    from mplchart.styles import Styler

    canvas = Canvas(figsize=(2, 2), style=Styler(stylesheet="classic"))
    root = canvas.root_axes()
    pane = canvas.new_axes("below")
    assert not root.xaxis.get_gridlines()[0].get_visible()
    assert not pane.yaxis.get_gridlines()[0].get_visible()
    plt.close(canvas.figure)


def test_grid_axis_selection():
    # axes.grid.axis composes with the root-x/pane-y structural split
    from mplchart.styles import Styler

    canvas = Canvas(figsize=(2, 2), style=Styler(rcparams={"axes.grid": True, "axes.grid.axis": "y"}))
    root = canvas.root_axes()
    pane = canvas.new_axes("below")
    assert not root.xaxis.get_gridlines()[0].get_visible()
    assert pane.yaxis.get_gridlines()[0].get_visible()
    plt.close(canvas.figure)


def test_root_patch_renders_facecolor():
    # the root patch is where axes.facecolor renders (panel styles like
    # ggplot draw grids against it); panes stay transparent overlays
    from mplchart.styles import Styler

    canvas = Canvas(figsize=(2, 2), style=Styler(rcparams={"axes.facecolor": "#e5e5e5"}))
    root = canvas.root_axes()
    pane = canvas.new_axes("below")
    assert root.patch.get_visible()
    assert not pane.patch.get_visible()
    plt.close(canvas.figure)


@pytest.mark.parametrize("position", ["above", "below"])
def test_new_axes_on_fresh_canvas_adds_secondary_pane(canvas, position):
    main = canvas.figure.axes[1]
    added = canvas.new_axes(position)
    assert canvas.panes() == [main, added]
    assert canvas.main_axes() is main
    assert canvas.get_axes() is added
    spec = added.get_subplotspec()
    assert spec.rowspan.start == (0 if position == "above" else 1)
    assert spec.get_gridspec().get_height_ratios() == (
        [0.2, 1.0] if position == "above" else [1.0, 0.2]
    )
