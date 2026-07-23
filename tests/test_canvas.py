"""Tests for the Canvas presentation plane."""

import pytest
import matplotlib.pyplot as plt

from mplchart.canvas import Canvas


@pytest.fixture
def canvas():
    canvas = Canvas()
    yield canvas
    plt.close(canvas.figure)


def test_canvas_creates_styled_root(canvas):
    assert len(canvas.figure.axes) == 1
    root = canvas.root_axes()
    assert root._label == "root"
    assert root.get_xmargin() == 0.0
    assert canvas.count_axes() == 0


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


def test_canvas_adopts_existing_figure():
    figure = plt.figure()
    figure.add_subplot()  # content to be cleared
    canvas = Canvas(figure=figure)
    assert canvas.figure is figure
    assert len(figure.axes) == 1  # cleared, root only
    plt.close(figure)


def test_get_axes_creates_main_pane(canvas):
    ax = canvas.get_axes()
    assert canvas.count_axes() == 1
    assert canvas.main_axes() is ax
    assert canvas.get_axes("same") is ax
    assert canvas.get_axes("main") is ax


def test_get_axes_above_below(canvas):
    main = canvas.get_axes()
    below = canvas.get_axes("below")
    above = canvas.get_axes("above")
    assert canvas.count_axes() == 3
    assert len({id(main), id(below), id(above)}) == 3
    assert canvas.main_axes() is main
    assert canvas.get_axes("same") is above  # last created pane is current


def test_get_axes_twinx(canvas):
    main = canvas.get_axes()
    twin = canvas.get_axes("twinx")
    assert twin is not main
    assert twin._label == "twinx"
    assert canvas.count_axes() == 1
    assert canvas.count_axes(include_twins=True) == 2


def test_get_axes_invalid_target(canvas):
    with pytest.raises(ValueError, match="Invalid target"):
        canvas.get_axes("bogus")


def test_resolve_color_scheme_lookup():
    from matplotlib.colors import to_hex

    canvas = Canvas(color_scheme={"macd": "red", "sma": "blue"})
    assert canvas.resolve_color("macd-12-26-9") == to_hex("red")  # prefix match
    assert canvas.resolve_color("sma") == to_hex("blue")  # raw match
    assert canvas.resolve_color("other", fallback="green") == to_hex("green")
    plt.close(canvas.figure)


def test_resolve_color_list_cycling():
    from matplotlib.colors import to_hex

    canvas = Canvas(color_scheme={"sma": ["red", "blue"]})
    ax = canvas.get_axes()
    assert canvas.resolve_color("sma", ax) == to_hex("red")
    assert canvas.resolve_color("sma", ax) == to_hex("blue")
    assert canvas.resolve_color("sma", ax) == to_hex("red")  # wraps around
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
    below = canvas.get_axes("below")
    below.plot(*view.series_xy(view.eval(lambda p: p["close"].rolling(20).mean())))

    assert canvas.count_axes() == 2
    xs = ax.lines[0].get_xdata()
    assert len(xs) == 100
    plt.close(canvas.figure)


def test_grid_default_look():
    # baseline DEFAULT_RC: root x-grid and pane y-grid on, alpha 0.4
    canvas = Canvas(figsize=(2, 2))
    root = canvas.root_axes()
    pane = canvas.get_axes("below")
    assert root.xaxis.get_gridlines()[0].get_visible()
    assert pane.yaxis.get_gridlines()[0].get_visible()
    assert root.xaxis.get_gridlines()[0].get_alpha() == 0.4
    plt.close(canvas.figure)


def test_grid_off_via_stylesheet():
    # the classic sheet sets axes.grid False — styles can disable the grid
    from mplchart.styles import Styler

    canvas = Canvas(figsize=(2, 2), style=Styler(stylesheet="classic"))
    root = canvas.root_axes()
    pane = canvas.get_axes("below")
    assert not root.xaxis.get_gridlines()[0].get_visible()
    assert not pane.yaxis.get_gridlines()[0].get_visible()
    plt.close(canvas.figure)


def test_grid_axis_selection():
    # axes.grid.axis composes with the root-x/pane-y structural split
    from mplchart.styles import Styler

    canvas = Canvas(figsize=(2, 2), style=Styler(rcparams={"axes.grid.axis": "y"}))
    root = canvas.root_axes()
    pane = canvas.get_axes("below")
    assert not root.xaxis.get_gridlines()[0].get_visible()
    assert pane.yaxis.get_gridlines()[0].get_visible()
    plt.close(canvas.figure)
