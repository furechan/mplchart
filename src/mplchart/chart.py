"""charting main module"""

import io
import warnings

import matplotlib.pyplot as plt

from collections import Counter
from functools import cached_property

from .colors import closest_color
from .utils import same_scale, get_info
from .layout import make_twinx, StandardLayout
from .mapper import RawDateMapper, DateIndexMapper
from .plotters import AutoPlotter


"""
How primitives/indicators are plotted
1) try plot_handler. No processing or no reindexing yet
2) call indicator / process data
3) call slice or reindex / map dataframe
3) replace indicator with wrapper if applicable
4) select/create axes
5) try indicator plot_result if applicable
6) otherwise plot series as lines
"""


class Chart:
    """
    Chart Object

    Args:
        title (str) : the chart title
        max_bars (int) : the maximum number of bars to plot
        start, end (datetime | str) :  the start and end date of the range to plot
        figsize (tuple) : the size of the figure

    Example:
        chart = Chart(title=tiltle, ...)
        chart.plot(prices, indicators)
    """

    mapper = None
    source_data = None
    next_target = None
    last_result = None
    layout = StandardLayout

    DEFAULT_FIGSIZE = (12, 9)

    def __init__(
        self,
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

        if title:
            self.set_title(title)

        if self.layout.use_tight_layout:
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
    def normalize(prices):
        """normalize prices dataframe"""
        prices = prices.rename(columns=str.lower).rename_axis(index=str.lower)
        return prices

    def init_mapper(self, data):
        """initalizes chart and mapper with price data"""

        if self.mapper is not None:
            warnings.warn("init_mapper was already called!", stacklevel=2)
            return

        if self.source_data is None:
            self.source_data = data

        if self.raw_dates:
            self.mapper = RawDateMapper(
                index=data.index, start=self.start, end=self.end, max_bars=self.max_bars
            )
        elif data is not None:
            self.mapper = DateIndexMapper(
                index=data.index, start=self.start, end=self.end, max_bars=self.max_bars
            )
        else:
            raise ValueError("Cannot create mapper. data is None!")

        if self.mapper:
            ax = self.root_axes()
            self.mapper.config_axes(ax)

    def rebase_data(self, data):
        if self.source_data is None:
            warnings.warn("No source data to rebase to!")
            return data

        source_data = self.mapper.slice(self.source_data)
        mapped_data = self.mapper.slice(data)

        if not len(data) or not len(source_data):
            warnings.warn("No intersection of data!")
            return data

        sp = source_data.loc[0].close
        mp = mapped_data.loc[0].close
        factor = sp / mp

        return data.filter(["open", "high", "low", "close"]) * factor

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

        if hasattr(indicator, "colors"):
            colors = indicator.colors
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

    def extract_df(self, data):
        """extract dataframe subset (deprecated)"""

        if self.mapper is None:
            self.init_mapper(data)

        return self.mapper.extract_df(data)

    def reindex(self, data):
        """re-index data"""

        if self.mapper is None:
            self.init_mapper(data)

        return self.mapper.reindex(data)

    def slice(self, data):
        """re-index and slice data"""

        if self.mapper is None:
            self.init_mapper(data)

        return self.mapper.slice(data)


    def map_date(self, date):
        """map date to value"""

        if self.mapper is None:
            raise ValueError("mapper was not configure yet!")

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

        ax = self.layout.init_vplot(self.figure)
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

        if indicator is None:
            return "same"

        target_pane = getattr(indicator, "target_pane", None)
        if target_pane is not None:
            return target_pane

        default_pane = get_info(indicator, "default_pane", None)
        if default_pane is not None:
            return default_pane

        if same_scale(indicator) and self.count_axes() <= 1:
            return "same"

        return "below"

    @staticmethod
    def valid_target(target):
        """whether the target bname is valid"""
        return target in ("main", "same", "samex", "twinx", "above", "below")

    def force_target(self, target):
        """force target for next get_axes"""

        warnings.warn(
            "Chart.force_target is legacy! Use axes modifier to select axes.",
            DeprecationWarning,
            stacklevel=2,
        )

        if not self.valid_target(target):
            raise ValueError("Invalid target %r" % target)

        self.next_target = target

    def get_axes(self, target=None, *, height_ratio=None):
        """
        select existing axes or creates new axes depending on target

        Args:
            target: one of "main", "same", twinx", "above", "below"
        """

        if self.next_target:
            target = self.next_target
            del self.next_target

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
            ax = self.layout.add_vplot(figure=figure)
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

            ax = self.layout.add_vplot(
                figure=figure, height_ratio=height_ratio, append=append
            )

        self.config_axes(ax)

        return ax

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

    def plot_indicator(self, data, indicator):
        """calculate and plot an indicator"""

        # Call the indicator's plot_handler if defined (before any calc)
        # this is the only location where plot_handler is called
        # plot_handler is currently defined only for Primitives
        # Note that data have not been mapped/sliced yet
        if hasattr(indicator, "plot_handler"):
            indicator.plot_handler(data, chart=self)
            return

        # Invoke indicator and compute result if indicator is callable
        # Result data is mapped to the charting view
        if callable(indicator):
            result = self.calc_result(data, indicator)
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

    def plot(self, prices, indicators, *, target=None, rebase=False):
        """plot list of indicators

        Parameters
        ----------
        prices: dataframe
            the prices data frame
        indicators: list of indicators
            list of indicators to plot
        """

        self.last_result = None

        if target is not None:
            self.force_target(target)

        prices = self.normalize(prices)

        if rebase:
            prices = self.rebase_data(prices)

        for indicator in indicators:
            self.plot_indicator(prices, indicator)

        self.add_legends()

    def plot_vline(self, date):
        """plot vertical line across all axes"""

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
        """render chart to the specific format"""
        if not self.figure.axes:
            self.get_axes()

        file = io.BytesIO()
        self.figure.savefig(file, format=format, dpi=dpi)
        result = file.getvalue()

        return result
