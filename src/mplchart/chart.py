""" charting main module """

import io
import warnings

import matplotlib.pyplot as plt

from .layout import make_twinx, StandardLayout, FixedLayout
from .mapper import RawDateMapper, DateIndexMapper
from .extalib import talib_function_check, talib_function_repr, talib_same_scale
from .wrappers import get_wrapper
from .styling import get_stylesheet
from .utils import series_xy


class Chart:
    """
    Chart Object

    Args:
        title (str) : the chart title
        max_bars (int) : the maximum number of bars to plot
        start, end (datetime | str) :  the start and end date of the range to plot
        figsize (tuple) : the size of the figure
        bgcolor (str): the backgorund color of the Chart, default='w'

    Example:
        chart = Chart(title=tiltle, ...)
        chart.plot(prices, indicators)
    """

    mapper_done = False
    source_data = None
    next_target = None
    last_indicator = None
    stylesheet = None
    layout = None
    mapper = None

    DEFAULT_FIGSIZE = (12, 9)

    @staticmethod
    def normalize(prices):
        prices = prices.rename(columns=str.lower).rename_axis(index=str.lower)
        return prices

    def __init__(
        self,
        title=None,
        max_bars=None,
        start=None,
        end=None,
        figure=None,
        figsize=None,
        bgcolor="w",
        use_calendar=False,
        holidays=None,
        style=None,
        fixed_layout=False,
    ):
        self.start = start
        self.end = end
        self.max_bars = max_bars
        self.holidays = holidays
        self.use_calendar = use_calendar

        if fixed_layout:
            warnings.warn("Fixed layout is deprecated!")
            self.layout = FixedLayout
        else:
            self.layout = StandardLayout

        self.stylesheet = get_stylesheet(style)

        if figure is None:
            figsize = figsize or self.DEFAULT_FIGSIZE
            figure = plt.figure(figsize=figsize, facecolor=bgcolor, edgecolor=bgcolor)
        else:
            figure.clf()

        self.figure = figure

        self.init_axes()

        if title:
            self.set_title(title)

        if self.layout.use_tight_layout:
            self.figure.set_layout_engine("tight")

    @staticmethod
    def valid_target(target):
        """whether the target bname is valid"""
        return target in ("main", "samex", "twinx", "above", "below")

    def inspect_data(self, data):
        """initalizes chart from data"""

        if self.source_data is None:
            self.source_data = data

        if not self.mapper_done:
            self.config_mapper(data=data)

    def rebase_data(self, data):
        if self.source_data is None:
            warnings.warn("No source data to rebase to!")
            return data

        source_data = self.mapper.slice(self.source_data)
        index = data.index.intersection(source_data.index)

        if not len(index):
            warnings.warn("No intersection of data!")
            return data

        dp = data.loc[index[0]]
        sp = source_data.loc[index[0]]
        factor = sp / dp

        return data.filter(["open", "high", "low", "close"]) * factor

    def extract_df(self, data):
        """extract dataframe view"""

        self.inspect_data(data)

        if self.mapper:
            return self.mapper.extract_df(data)

        return data

    def map_date(self, date):
        """map date to value"""

        if not self.mapper_done:
            raise ValueError("mapper was not configure yet!")

        if self.mapper:
            return self.mapper.map_date(date)

        return date

    def set_title(self, title):
        """Sets chart title on root axes. Must be called after init_axes!"""

        if title is None:
            return

        # self.figure.suptitle(title)

        ax = self.root_axes()
        ax.set_title(title)

    def config_mapper(self, *, data=None):
        """Configures the date mapper from the original data"""

        self.mapper_done = True

        if self.use_calendar:
            self.mapper = RawDateMapper(
                start=self.start, end=self.end, max_bars=self.max_bars
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

    def config_axes(self, ax, root=False):
        """configures axes"""

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
        """returns root axes, usualy axes[0]"""

        if not self.figure.axes:
            warnings.warn("root_axes called before init_axes!")
            self.init_axes()

        return self.figure.axes[0]

    def main_axes(self):
        """returns main axes, usualy axes[1]"""

        if not self.figure.axes:
            warnings.warn("main_axes called before init_axes!")
            self.init_axes()

        if len(self.figure.axes) > 1:
            ax = self.figure.axes[1]
        else:
            ax = self.get_axes()

        return ax

    def default_pane(self, indicator):
        """return the default pane to use for indicator"""

        if talib_function_check(indicator):
            same_scale = talib_same_scale(indicator)
        else:
            same_scale = getattr(indicator, "same_scale", False)

        if same_scale and self.count_axes() <= 1:
            return "samex"

        return "below"

    def force_target(self, target):
        """force target for next get_axes"""

        if not self.valid_target(target):
            raise ValueError("Invalid target %r" % target)

        self.next_target = target

    def get_axes(self, target=None, *, height_ratio=None):
        """returns or creates axes at given target"""

        if self.next_target:
            target = self.next_target
            del self.next_target

        if target is None:
            target = "samex"

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

            if target == "samex":
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
        self.reset_stylesheet()

        return ax

    def dump_axes(self):
        for i, ax in enumerate(self.figure.axes):
            label = getattr(ax, "_label") or "none"
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            print(i, label, xlim, ylim)

    def count_axes(self, include_root=False, include_twins=False):
        """ " counts axes that are neither root or twinx"""
        count = 0
        for ax in self.figure.axes:
            label = getattr(ax, "_label", None)
            if label == "root" and not include_root:
                continue
            if label == "twinx" and not include_twins:
                continue
            count += 1
        return count

    def reset_stylesheet(self):
        """resets stylesheet"""
        return self.stylesheet.reset()

    def get_setting(self, key, section, fallback=None):
        """gets setting from stylesheet"""
        return self.stylesheet.get_setting(key, section, fallback=fallback)

    def get_settings(self, key, **kwargs):
        """gets settings from stylesheet matching kwargs"""
        return self.stylesheet.get_settings(key, **kwargs)

    def get_label(self, indicator):
        """returns label to use for indicator"""

        if talib_function_check(indicator):
            return talib_function_repr(indicator)

        return getattr(indicator, "__name__", str(indicator))

    def plot_indicator(self, data, indicator):
        """calculates and plots an indicator"""

        # Call the indicator's plot_handler if defined (before any calc)
        # Note this is the only location where plot_handler is called
        if hasattr(indicator, "plot_handler"):
            indicator.plot_handler(data, chart=self)
            return

        # Invoke indicator and compute result if indicator is callable
        if callable(indicator):
            self.last_indicator = indicator
            result = indicator(data)
            result = self.extract_df(result)
        else:
            raise ValueError(f"Indicator {indicator!r} not callable")

        # Calling wrapper plot_result if applicable
        # Note target axes has not been selected yet
        # The wrapper will do the axes selection calling get_axes
        wrapper = get_wrapper(indicator)
        if wrapper is not None and wrapper.check_result(result):
            wrapper.plot_result(result, chart=self)
            return

        # Select axes according to indicator properties (see same_scale)
        target = self.default_pane(indicator)
        ax = self.get_axes(target)

        # Calling indicator plot_result if present
        # Note here we are calling plot_result with an axes
        # This does not seem to be happening ever !
        if hasattr(indicator, "plot_result"):
            warnings.warn("Calling plot_result on {indicator!r} with ax={ax!r}")
            indicator.plot_result(result, self, ax=ax)
            return

        label = self.get_label(indicator)
        xv, yv = series_xy(result)
        ax.plot(xv, yv, label=label)

    def add_legends(self):
        """adds legends to all axes"""
        for ax in self.figure.axes:
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(loc="upper left")

    def plot(self, prices, indicators, *, target=None, rebase=False):
        """plots a list of indicators

        Parameters
        ----------
        prices: dataframe
            the prices data frame
        indicators: list of indicators
            list of indciators to plot

        """

        if target is not None:
            self.force_target(target)

        prices = self.normalize(prices)

        if rebase:
            prices = self.rebase_data(prices)

        for indicator in indicators:
            self.plot_indicator(prices, indicator)

        self.add_legends()

    def plot_vline(self, date):
        """plots a vertical line across all axes"""

        if not self.figure.axes:
            raise RuntimeError("axes not initialized!")

        ax = self.root_axes()
        xv = self.map_date(date)

        ax.axvline(xv, linestyle="dashed")

    def show(self):
        """shows the chart"""
        if not self.figure.axes:
            self.get_axes()

        # figure.show() seems only to work if figure was not created by pyplot!
        plt.show()

    def render(self, format="svg"):
        """renders the chart to the specific format"""
        if not self.figure.axes:
            self.get_axes()

        file = io.BytesIO()
        self.figure.savefig(file, format=format)
        result = file.getvalue()

        return result
