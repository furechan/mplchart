"""charting main module"""

import warnings

from .canvas import Canvas
from .dataview import get_view
from .dateaxis import config_date_axis
from .utils import detect_backend, is_indicator_like, is_series_data
from .utils import normalize_prices, check_prices
from .primitives.autoplot import AutoPlot


"""
How primitives/indicators are plotted
1) try apply_to_chart. No processing or no reindexing yet
2) call indicator / process data
3) call slice / map index and slice data to charting view
3) replace indicator with wrapper if applicable
4) select/create axes
5) try indicator plot_result if applicable
6) otherwise plot series as lines
"""


class Chart:
    """Main charting class for creating financial charts with technical indicators.

    Composes a data view (``chart.view``) and a presentation canvas
    (``chart.canvas``). Prices are required at initialization; the data view
    is created lazily on first access (see ``get_view``) and cached. Calls
    to ``plot()`` add indicators to existing or new panes.

    Args:
        prices (DataFrame): OHLCV prices DataFrame (pandas or polars), used to
            initialize the data view. Required.
        title (str, optional): Chart title displayed above the main pane.
        max_bars (int, optional): Maximum number of bars to display. When set,
            only the most recent ``max_bars`` bars are shown.
        start (datetime or str, optional): Start of the display range.
        end (datetime or str, optional): End of the display range.
        figure (Figure, optional): Existing matplotlib Figure to draw on.
            The figure is cleared before use.
        figsize (tuple, optional): Figure size as ``(width, height)`` in inches.
            Defaults to ``(12, 9)``.
        normalize (bool): If True, normalize the prices DataFrame first
            (lowercase columns, promote a date/datetime column to the index).
            Defaults to False.
        raw_dates (bool, optional): If True, use raw-dates mode — the
            x-axis coordinates are actual datetime values and matplotlib
            handles date formatting natively. Defaults to False, which maps
            dates to integer rownum positions with a custom date formatter
            (eliminating weekend/holiday gaps).
        style (optional): Style spec, normalized via ``get_styler`` — a
            shipped style name (see ``styles.available_styles()``), a
            matplotlib stylesheet name, a spec mapping
            (``stylesheet``/``rc``/``settings``), a ``Style``, or a
            prebuilt ``Styler``. Defaults to the ``"mplchart"`` style.
            Styles are total — ambient rcParams never affect the chart.
        color_scheme: Deprecated and ignored — use ``style=`` with settings
            (e.g. ``Styler(settings={"sma.color": "red"})``).

    Examples:
        chart = Chart(prices, title="AAPL", max_bars=252)
        chart.plot([Candlesticks(), SMA(50), Volume()])
        chart.show()
    """

    _prices = None
    _view = None

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
        normalize=False,
        raw_dates=False,
        style=None,
        color_scheme=(),
    ):
        if color_scheme:
            warnings.warn(
                "color_scheme is deprecated and ignored — use style= with "
                "settings (e.g. Styler(settings={'sma.color': 'red'}))",
                DeprecationWarning,
                stacklevel=2,
            )

        self.start = start
        self.end = end
        self.max_bars = max_bars
        self.raw_dates = raw_dates

        self.canvas = Canvas(figsize=figsize, figure=figure, title=title, style=style)

        if prices is None:
            raise ValueError("Prices data must be provided at initialization!")

        self.init_prices(prices, normalize=normalize)

    @property
    def figure(self):
        """The canvas figure."""
        return self.canvas.figure

    @property
    def view(self):
        """The chart data view — created lazily on first access (see ``get_view``)."""
        return self.get_view()

    @property
    def mapper(self):
        """Deprecated alias for the data view, kept for compatibility."""
        warnings.warn(
            "chart.mapper is deprecated, use chart.view instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.view

    def init_prices(self, prices, normalize: bool = False):
        """Prepare and store the chart price data.

        The data view is not created here — ``get_view`` creates it lazily
        on first access.

        Args:
            prices (DataFrame): OHLCV prices DataFrame with a datetime index
                or a ``date``/``datetime`` column.
        """

        if self._prices is not None:
            warnings.warn("init_prices was already called!", stacklevel=2)
            return

        if normalize:
            prices = normalize_prices(prices)

        check_prices(prices)

        self.backend = detect_backend(prices)
        self._prices = prices

        return prices

    def get_view(self, transform=None):
        """Return the chart data view, creating and caching it on first call.

        The first call creates the view from the chart prices and installs
        the date-axis machinery; later calls return the cached view.

        Args:
            transform (callable, optional): prices transform (e.g. a renko or
                point-and-figure calc) applied to the prices before the view
                is created. Only allowed while the view does not exist yet —
                the first view access wins. Incompatible with ``raw_dates``
                (transformed frames only make sense on the rownum x-axis).
        """

        if self._view is not None:
            if transform is not None:
                raise ValueError("view already created — pass transform before first use")
            return self._view

        prices = self._prices

        if transform is not None:
            if self.raw_dates:
                raise ValueError("transform is incompatible with raw_dates!")
            prices = transform(prices)
            check_prices(prices)

        self._view = get_view(
            prices, raw_dates=self.raw_dates, start=self.start, end=self.end, max_bars=self.max_bars
        )

        if not self._view.raw_dates:
            config_date_axis(self.canvas.root_axes(), self._view.dates)

        return self._view

    def pane(self, target="below", *, height_ratio=None, yticks=None):
        """create or select a pane and return self for chaining

        Args:
            target: one of "same", "above", "below", "twinx"
            height_ratio: relative height of the new pane
            yticks: tuple of y-axis tick values (also draws heavy grid lines)
        """

        ax = self.canvas.get_axes(target, height_ratio=height_ratio)

        if yticks:
            ax.set_yticks(yticks)
            ax.grid(axis="y", which="major", linestyle="-", linewidth=2)

        return self

    def plot_indicator(self, indicator):
        """calculate and plot an indicator"""

        # All primitive drawing runs inside the styler's rc context — this is
        # the single apply_to_chart dispatch site (vline/hline route through)
        with self.canvas.styler.context():
            self._plot_indicator(indicator)

    def _plot_indicator(self, indicator):
        """``plot_indicator`` body — runs inside the styler's rc context."""

        # Call the primitive's apply_to_chart if defined (before any calc)
        # this is the only location where apply_to_chart is called
        # apply_to_chart is currently defined only for Primitives
        # Note that data have not been mapped/sliced yet
        if hasattr(type(indicator), "apply_to_chart"):
            indicator.apply_to_chart(self)
            return

        # Anything else (polars Expr, pandas Expression, tuple-of-Expr,
        # callable, or already-computed series data) is wrapped in the default
        # AutoPlot primitive and dispatched through its apply_to_chart — the
        # single auto-plot code path.
        if is_indicator_like(indicator) or is_series_data(indicator):
            AutoPlot(indicator).apply_to_chart(self)
            return

        raise ValueError(f"Indicator {indicator!r} not callable")

    def plot(self, *args):
        """Plot one or more indicators onto the chart.

        Args:
            *args: Any number of indicators or lists of indicators. Indicators may be
                ``Indicator`` instances, ``Primitive`` instances, or any callable
                that accepts a prices DataFrame. Use ``pane()`` or the ``Pane``
                primitive to select or create the target pane.

        Returns:
            Chart: ``self``, for method chaining.

        Examples:
            chart.plot(Candlesticks(), Volume())
            chart.pane("above").plot(RSI(14))
            chart.plot(Pane("below"), MACD())
        """

        indicators = [
            y for arg in args for y in (arg if isinstance(arg, list) else (arg,))
        ]

        if not indicators:
            raise ValueError("No indicators provided!")

        # ensure a main pane exists — root-drawing primitives (e.g. Stripes)
        # never create one themselves
        self.canvas.get_axes()

        for indicator in indicators:
            self.plot_indicator(indicator)

        self.canvas.add_legends()

        return self

    def vline(self, date, *, color=None, linestyle=None):
        """Draw a vertical line across all panes at the given date.

        Args:
            date: date or date string for the vertical line position
            color: line color (default: matplotlib grid.color)
            linestyle: line style (default: matplotlib grid.linestyle)
        """
        from .primitives.vline import VLine

        self.plot_indicator(VLine(date, color=color, linestyle=linestyle))
        return self

    def plot_vline(self, date):
        """Legacy alias for vline(), kept for compatibility. Use vline() instead."""
        warnings.warn(
            "plot_vline() is a legacy alias, use vline() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.vline(date)

    def hline(self, value, *, color=None, linestyle=None):
        """Draw a horizontal line on the current pane at the given value.

        Args:
            value: y-axis value for the horizontal line position
            color: line color (default: matplotlib grid.color)
            linestyle: line style (default: matplotlib grid.linestyle)
        """
        from .primitives.hline import HLine

        self.plot_indicator(HLine(value, color=color, linestyle=linestyle))
        return self

    def show(self):
        """show chart"""
        self.canvas.show()

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
        return self.canvas.render(format=format, dpi=dpi)
