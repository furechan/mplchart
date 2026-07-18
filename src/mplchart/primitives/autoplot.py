"""AutoPlot primitive — default auto-plotting with small overrides"""

from ..model.primitive import BindingPrimitive
from ..utils import get_label, get_metadata


class AutoPlot(BindingPrimitive):
    """Default plotter primitive.

    Auto-plots an expression or indicator with default styling. Used implicitly
    when plotting anything that is not already a ``Primitive``; can also be
    applied explicitly to override the legend label.

    Args:
        indicator: indicator or expression to plot. Can also be bound via ``@``.
        label (str): override the legend label. When ``None``, the label is
            derived from the expression/indicator via ``get_label``.

    Examples:
        chart.plot(SMA(20))                                # implicit AutoPlot
        chart.plot(AutoPlot(SMA(20), label="short_ma"))    # explicit override
        chart.plot(MACD() @ AutoPlot(label="macd"))        # operator form
    """

    def __init__(self, indicator=None, *, label: str | None = None):
        super().__init__(indicator)
        self.label = label

    def apply_to_chart(self, chart):
        ax = chart.get_axes()

        data = chart.calc_result(self.required_indicator())

        group_label = self.label if self.label is not None else get_label(self.indicator)
        columns = list(data.columns) if hasattr(data, "columns") else []

        if not columns:
            line_style = get_metadata(self.indicator, "line_style", "solid")
            if line_style == "bars":
                self._plot_bars(chart, data, ax, group_label, label=group_label)
            elif line_style == "area":
                self._plot_area(chart, data, ax, group_label, label=group_label)
            else:
                self._plot_line(chart, data, ax, group_label, style=line_style, label=group_label)
            return

        bands: dict[str, str] = {}
        counter = 0
        current_label = group_label

        for item in columns:
            if counter > 0:
                current_label = None

            if item in ("upperband", "lowerband", "middleband"):
                bands[item.removesuffix("band")] = item
                continue

            if item.endswith("hist"):
                self._plot_bars(chart, data, ax, item, label=current_label)
                continue

            self._plot_line(chart, data, ax, item, label=current_label)
            counter += 1

        if bands:
            self._plot_bands(chart, data, ax, **bands, label=group_label)

    def _series(self, data, item):
        """Extract a named column as a Series, or return data unchanged if 1-D."""
        if hasattr(data, "columns"):
            col = item if item is not None else data.columns[0]
            return data[col]
        return data

    def _plot_line(self, chart, data, ax, item, *, style=None, label=None):
        if style == "marker":
            linestyle = "none"
            marker = "."
        else:
            linestyle = style
            marker = None

        color = chart.get_color(item, ax, fallback="line")
        xv, yv = chart.series_xy(self._series(data, item))
        ax.plot(xv, yv, label=label, linestyle=linestyle, marker=marker, color=color)

    def _plot_bars(self, chart, data, ax, item, *, label=None):
        color = chart.get_color(item, ax, fallback="fill")
        xv, yv = chart.series_xy(self._series(data, item))
        ax.bar(xv, yv, color=color, alpha=0.5, width=0.8, label=label)

    def _plot_area(self, chart, data, ax, item, *, label=None):
        color = chart.get_color(item, ax, fallback="fill")
        xv, yv = chart.series_xy(self._series(data, item))
        ax.fill_between(xv, yv, 0, label=label, interpolate=True, color=color, alpha=0.5)

    def _plot_bands(self, chart, data, ax, upper, lower, middle=None, label=None):
        key = get_label(self.indicator)
        color = chart.get_color(key, ax, fallback="line")

        if middle:
            xv, mv = chart.series_xy(self._series(data, middle))
            ax.plot(xv, mv, color=color, linestyle="dashed")

        xv, lv = chart.series_xy(self._series(data, lower))
        xv, uv = chart.series_xy(self._series(data, upper))

        ax.plot(xv, lv, color=color, linestyle="dotted")
        ax.plot(xv, uv, color=color, linestyle="dotted")
        ax.fill_between(
            xv, lv, uv, color=color, interpolate=True, alpha=0.2, label=label
        )
