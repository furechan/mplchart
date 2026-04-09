"""charting main module"""

import io
import warnings

import numpy as np
import matplotlib.pyplot as plt

from collections import Counter
from functools import cached_property

from .colors import closest_color
from .utils import same_scale, get_metadata, detect_backend, normalize_columns, extract_datetime, is_expr
from .layout import make_twinx, init_vplot, add_vplot
from .mapper import RawDateMapper, DateIndexMapper
from .model import PolarsExprIndicator
from .plotters import AutoPlotter


USE_TIGHT_LAYOUT = True

"""
How primitives/indicators are plotted
1) try plot_handler. No processing or no reindexing yet
2) call indicator / process data
3) call slice / map index and slice data to charting view
3) replace indicator with wrapper if applicable
4) select/create axes
5) try indicator plot_result if applicable
6) otherwise plot series as lines
"""



class Chart:
    """Main charting class for creating financial charts with technical indicators.

    Creates a matplotlib figure with one or more panes. The first call to
    ``plot()`` initializes the date mapper from the prices DataFrame. Subsequent
    calls add indicators to existing or new panes.

    Args:
        prices (DataFrame, optional): OHLCV prices DataFrame used to initialize
            the date mapper immediately. Can also be passed to ``plot()`` later.
        title (str, optional): Chart title displayed above the main pane.
        max_bars (int, optional): Maximum number of bars to display. When set,
            only the most recent ``max_bars`` bars are shown.
        start (datetime or str, optional): Start of the display range.
        end (datetime or str, optional): End of the display range.
        figure (Figure, optional): Existing matplotlib Figure to draw on.
            The figure is cleared before use.
        figsize (tuple, optional): Figure size as ``(width, height)`` in inches.
            Defaults to ``(12, 9)``.
        holidays (list, optional): List of dates to exclude from the x-axis
            when using the integer date mapper.
        color_scheme (dict or iterable of pairs, optional): Mapping of color
            role names to color values used to override default colors (e.g.
            ``colorup``, ``colordn``, ``bgcolor``).

    Examples:
        chart = Chart(title="AAPL", max_bars=252)
        chart.plot(prices, [Candlesticks(), SMA(50), Volume()])
        chart.show()
    """

    mapper = None
    prices = None
    last_result = None
    force_target = None

    DEFAULT_FIGSIZE = (12, 9)

    def __init__(
        self,
        prices=None,
        *,
        title=None,
        max_bars=None,
        start=None,
        end=None,
        figure=None,
        figsize=None,
        bgcolor=None,
        holidays=None,
        raw_dates=False,
        color_scheme=(),
    ):
        self.start = start
        self.end = end
        self.figsize = figsize
        self.max_bars = max_bars
        self.holidays = holidays
        self.raw_dates = raw_dates
        self.color_scheme = dict(color_scheme)

        if raw_dates:
            warnings.warn(
                "raw_dates parameter is deprecated.",
                DeprecationWarning,
                stacklevel=2,
            )

        if bgcolor is not None:
            warnings.warn(
                "bgcolor parameter is deprecated. Use matplotlib styles instead!",
                DeprecationWarning,
                stacklevel=2,
            )

        if figure is not None:
            figure.clf()
            self.figure = figure

        self.init_axes()

        if prices is not None:
            self.init_mapper(prices)
        else:
            raise ValueError("Prices data must be provided at initialization!")

        if title:
            self.set_title(title)

        if USE_TIGHT_LAYOUT:
            self.figure.set_layout_engine("tight")

    @cached_property
    def counter(self):
        return Counter()

    @cached_property
    def figure(self):
        figsize = self.figsize or self.DEFAULT_FIGSIZE
        # bgcolor = self.get_color("bgcolor")
        # return plt.figure(figsize=figsize, facecolor=bgcolor, edgecolor=bgcolor)
        return plt.figure(figsize=figsize)

    @staticmethod
    def prepare_pandas(prices):
        """prepare pandas prices dataframe"""

        prices = prices.rename(columns=str.lower)

        if "datetime" in prices.columns:
            prices = prices.set_index("datetime")
        elif "date" in prices.columns:
            prices = prices.set_index("date")
        else:
            prices = prices.rename_axis(index=str.lower)

        return prices

    @staticmethod
    def prepare_polars(prices):
        """prepare polars prices dataframe"""

        return normalize_columns(prices)

    @staticmethod
    def prepare(prices):
        """prepare prices dataframe for charting"""

        match detect_backend(prices):
            case "polars":
                return Chart.prepare_polars(prices)
            case "pandas":
                return Chart.prepare_pandas(prices)
            case backend:
                raise ValueError(f"Unsupported backend {backend!r}")


    def init_mapper(self, prices):
        """Initialize the chart date mapper with price data.

        Normalizes column names to lowercase, sets the index, and
        creates the appropriate date mapper (integer-based or raw-date).

        Args:
            prices (DataFrame): OHLCV prices DataFrame with a datetime index
                or a ``date``/``datetime`` column.
        """

        if self.mapper is not None:
            warnings.warn("init_mapper was already called!", stacklevel=2)
            return

        if self.prices is not None:
            warnings.warn("init_mapper was already called with different data!", stacklevel=2)

        prices = self.prepare(prices)

        self.prices = prices
        self.backend = detect_backend(prices)

        datetime_array = extract_datetime(prices)

        if self.raw_dates:
            self.mapper = RawDateMapper(
                index=prices.index, start=self.start, end=self.end, max_bars=self.max_bars
            )
        else:
            self.mapper = DateIndexMapper(
                datetime_array=datetime_array, start=self.start, end=self.end, max_bars=self.max_bars
            )

        if self.mapper:
            ax = self.root_axes()
            self.mapper.config_axes(ax)

        return prices


    def next_line_color(self, ax):
        """Next line color either text.color or cycled color"""
        handles, _ = ax.get_legend_handles_labels()
        if len(handles):
            return ax._get_lines.get_next_color()
        else:
            return plt.rcParams["text.color"]

    def next_fill_color(self, ax):
        """Next cycled color for fill"""
        return ax._get_patches_for_fill.get_next_color()

    def get_color(self, name, ax=None, indicator=None, *, fallback=None):
        """Lookup color through indicator and color_scheme"""

        color = fallback

        colors = self.color_scheme
        if colors and name in colors:
            color = colors[name] or color

        if isinstance(color, list):
            ckey = ax, name
            count = self.counter[ckey]
            self.counter[ckey] += 1
            color = color[count % len(color)] if color else None

        if color and color.startswith("~"):
            color = closest_color(color.removeprefix("~"))

        if color == "line":
            color = self.next_line_color(ax)
        elif color == "fill":
            color = self.next_fill_color(ax)

        return color


    def slice(self, data):
        """re-index and slice data"""

        if self.mapper is None:
            raise ValueError("Date mapper was not configured yet. prices not provided!")

        self.window = self.mapper.calc_window()
        return self.mapper.slice(data)

    def plot_xy(self, data):
        """Return (xv, yv) numpy arrays for a same-length series (pandas or polars).

        Applies the current view window and maps row numbers to x-coordinates.
        Use this instead of chart.slice() + series_xy() in primitives.
        """
        window = self.mapper.calc_window()
        self.window = window
        return self.mapper.series_xy(np.asarray(data), window)

    def map_date(self, date):
        """map date to value"""

        if self.mapper is None:
            raise ValueError("Date mapper was not configured yet. prices not provided!")

        return self.mapper.map_date(date)

    def set_title(self, title):
        """Set chart title on root axes. Must be called after init_axes!"""

        if title is None:
            return

        # self.figure.suptitle(title)

        ax = self.root_axes()
        ax.set_title(title)

    def config_axes(self, ax, root=False):
        """configure axes"""

        ax.set_xmargin(0.0)
        ax.set_axisbelow(True)
        ax.patch.set_visible(
            False
        )  # make patch trasnparent to see through root axes drawings

        # x grid is displayed by the root axes
        # y grid is displayed by the sub axes

        if root:
            ax.xaxis.grid(True, alpha=0.4)
            ax.yaxis.grid(False)
            ax.tick_params(left=False, labelleft=False)
            return

        ax.xaxis.grid(False)
        ax.yaxis.grid(True, alpha=0.4)
        ax.yaxis.tick_right()

        # remove ticks on non-root axes
        ax.tick_params(
            axis="x",  # changes apply to the x-axis
            which="both",  # both major and minor ticks are affected
            bottom=False,  # ticks along the bottom edge are off
            top=False,  # ticks along the top edge are off
            labelbottom=False,
        )  # labels along the bottom edge are off

    def init_axes(self):
        """create root axes"""

        # Create a root axes with label 'root'
        # Must be called after the layout is set !
        # The root axes is needed before set_title, config_mapping

        ax = init_vplot(self.figure)
        self.config_axes(ax, root=True)

    def root_axes(self):
        """root axes (usualy axes[0])"""

        if not self.figure.axes:
            warnings.warn("root_axes called before init_axes!")
            self.init_axes()

        return self.figure.axes[0]

    def main_axes(self):
        """main axes (usualy axes[1])"""

        if not self.figure.axes:
            warnings.warn("main_axes called before init_axes!")
            self.init_axes()

        if len(self.figure.axes) > 1:
            ax = self.figure.axes[1]
        else:
            ax = self.get_axes()

        return ax

    def get_target(self, indicator):
        """target axes for indicator"""

        if self.force_target:
            return self.force_target

        if indicator is None:
            return "same"

        target_pane = getattr(indicator, "target_pane", None)
        if target_pane is not None:
            return target_pane

        default_pane = get_metadata(indicator, "default_pane", None)
        if default_pane is not None:
            return default_pane

        if same_scale(indicator) and self.count_axes() <= 1:
            return "same"

        return "below"

    @staticmethod
    def valid_target(target):
        """whether the target bname is valid"""
        return target in ("main", "same", "samex", "twinx", "above", "below")

    def get_axes(self, target=None, *, height_ratio=None):
        """
        select existing axes or creates new axes depending on target

        Args:
            target: one of "main", "same", twinx", "above", "below"
        """

        if target is None:
            target = "same"

        if not self.valid_target(target):
            raise ValueError("Invalid target %r" % target)

        figure = self.figure

        if not figure.axes:
            self.init_axes()

        # ignore root and volume axes
        axes = [ax for ax in self.figure.axes if ax._label not in ("root", "twinx")]

        if not axes:
            ax = add_vplot(figure=figure)
        else:
            if target == "main":
                return axes[0]

            if target in ("same", "samex"):
                return axes[-1]

            if target == "twinx":
                return make_twinx(axes[-1])

            append = target == "below"

            if not height_ratio:
                height_ratio = 0.2

            ax = add_vplot(
                figure=figure, height_ratio=height_ratio, append=append
            )

        self.config_axes(ax)

        return ax

    def pane(self, target="below", *, height_ratio=None):
        """get axes for target or None for all axes except root"""

        self.get_axes(target, height_ratio=height_ratio)

        return self

    def dump_axes(self):
        for i, ax in enumerate(self.figure.axes):
            label = getattr(ax, "_label") or "none"
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            print(i, label, xlim, ylim)

    def count_axes(self, include_root=False, include_twins=False):
        """count axes that are neither root or twinx"""
        count = 0
        for ax in self.figure.axes:
            label = getattr(ax, "_label", None)
            if label == "root" and not include_root:
                continue
            if label == "twinx" and not include_twins:
                continue
            count += 1
        return count

    def calc_result(self, prices, indicator):
        """calculate indicator result saving last result"""

        if indicator is not None:
            result = indicator(prices)
            self.last_result = result
        elif self.last_result is not None:
            result = self.last_result
        else:
            result = prices
            
        return result

    def plot_indicator(self, indicator):
        """calculate and plot an indicator"""

        prices = self.prices

        if self.prices is None:
            raise ValueError("No prices data provided!")

        prices = self.prices

        # wrap polars Expr / tuple of Expr in PolarsExprIndicator (no polars import)
        if is_expr(indicator):
            indicator = PolarsExprIndicator(indicator)
        elif isinstance(indicator, tuple) and all(is_expr(e) for e in indicator):
            indicator = PolarsExprIndicator(indicator)

        # Call the indicator's plot_handler if defined (before any calc)
        # this is the only location where plot_handler is called
        # plot_handler is currently defined only for Primitives
        # Note that data have not been mapped/sliced yet
        if hasattr(indicator, "plot_handler"):
            indicator.plot_handler(prices, chart=self)
            return

        # Invoke indicator and compute result if indicator is callable
        # Result data is mapped to the charting view
        if callable(indicator):
            result = self.calc_result(prices, indicator)
            result = self.slice(result)
        else:
            raise ValueError(f"Indicator {indicator!r} not callable")

        plotter = AutoPlotter(self, indicator, result)
        plotter.plot_all()


    def add_legends(self):
        """add legends to all axes"""
        for ax in self.figure.axes:
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(loc="upper left")

    def plot(self, *args, target: str | None = "same"):
        """Plot one or more indicators onto the chart.

        Args:
            *args: Any number of indicators or lists of indicators. Indicators may be
                ``Indicator`` instances, ``Primitive`` instances, or any callable
                that accepts a prices DataFrame.
            target (str or None): Target pane for the first indicator in this
                call. One of ``"same"``, ``"main"``, ``"above"``, ``"below"``,
                ``"twinx"``. Use ``None`` to let each indicator choose its own
                pane. Defaults to ``"same"``.

        Returns:
            Chart: ``self``, for method chaining.

        Examples:
            chart.plot(Candlesticks(), Volume())
            chart.plot(RSI(14), target="above)
            chart.plot(MACD(), target="below")
        """
        
        indicators = [
            y for arg in args for y in (arg if isinstance(arg, list) else (arg,))
        ]

        if not indicators:
            raise ValueError("No indicators provided!")

        if self.prices is None:
            raise ValueError("Np prices data provided!")
    
        self.last_result = None

        if target:
            self.get_axes(target)
            self.force_target = "same"
        else:
            self.force_target = None

        for indicator in indicators:
            self.plot_indicator(indicator)

        self.add_legends()

        return self

    def plot_vline(self, date):
        """Plot a vertical dashed line across all panes at the given date.

        Args:
            date (datetime or str): The date at which to draw the vertical line.
        """

        if not self.figure.axes:
            raise RuntimeError("axes not initialized!")

        ax = self.root_axes()
        xv = self.map_date(date)

        ax.axvline(xv, linestyle="dashed")

    def show(self):
        """show chart"""
        if not self.figure.axes:
            self.get_axes()

        # figure.show() seems only to work if figure was not created by pyplot!
        plt.show()

    def render(self, format="svg", *, dpi="figure"):
        """Render the chart to bytes in the specified image format.

        Args:
            format (str): Output format, e.g. ``"svg"``, ``"png"``, ``"pdf"``.
                Defaults to ``"svg"``.
            dpi (float or str): Resolution in dots per inch. Pass ``"figure"``
                to use the figure's own DPI setting. Defaults to ``"figure"``.

        Returns:
            bytes: The rendered image as a byte string.
        """
        if not self.figure.axes:
            self.get_axes()

        file = io.BytesIO()
        self.figure.savefig(file, format=format, dpi=dpi)
        result = file.getvalue()

        return result
