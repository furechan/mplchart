"""auto indicator ploters"""

import numpy as np
import matplotlib.pyplot as plt

from .utils import get_name, get_label, get_info


class AutoPlotter():
    def __init__(self, chart, indicator, data, ax=None):
        if ax is None:
            target = chart.get_target(indicator)
            ax = chart.get_axes(target)
        self.chart = chart
        self.indicator = indicator
        self.data = data
        self.ax = ax

    def next_line_color(self, ax):
        handles, _ = ax.get_legend_handles_labels()
        if len(handles):
            return ax._get_lines.get_next_color()
        else:
            return plt.rcParams["text.color"]

    def next_fill_color(self, ax):
        return ax._get_patches_for_fill.get_next_color()

    def get_columns(self):
        if hasattr(self.data, "columns"):
            return list(self.data.columns)
        
        return ()
    

    def series_xy(self, item=None):   # ignore item for series !!!
        """split data into x, y arrays"""
        # ignore item if data is a series !
        if self.data.__class__.__name__ == "Series":
            series = self.data
        elif item is not None:
            series = self.data[item]
        else:
            series = self.data.iloc[:, 0]
        return series.index.values, series.values


    def plot_line(self, item, *, style=None, label=None):
        if style == "marker":
            linestyle = "none"
            marker = "."
        else:
            linestyle = style
            marker = None

        color = self.chart.get_color(item, self.ax, self.indicator, fallback="line")
        xv, yv = self.series_xy(item)
        self.ax.plot(xv, yv, label=label, linestyle=linestyle, marker=marker, color=color)

    def plot_bars(self, item, *, label=None):
        color = self.chart.get_color(item, self.ax, self.indicator, fallback="fill")
        xv, yv = self.series_xy(item)
        self.ax.bar(xv, yv, color=color, alpha=0.5, width=0.8, label=label)

    def plot_area(self, item, *, label=None):
        color = self.chart.get_color(item, self.ax, self.indicator, fallback="fill")
        xv, yv = self.series_xy(item)
        self.ax.fill_between(xv, yv, 0, label=label, interpolate=True, color=color, alpha=0.5)


    def plot_bands(self, upper, lower, middle=None, label=None):
        name = get_name(self.indicator).lower()
        color = self.chart.get_color(name, self.ax, self.indicator, fallback="line")

        if middle:
            xv, mv = self.series_xy(middle)
            self.ax.plot(xv, mv, color=color, linestyle="dashed")

        xv, lv = self.series_xy(lower)
        xv, uv = self.series_xy(upper)

        self.ax.plot(xv, lv, color=color, linestyle="dotted")
        self.ax.plot(xv, uv, color=color, linestyle="dotted")

        self.ax.fill_between(
            xv, lv, uv, color=color, interpolate=True, alpha=0.2, label=label
        )

    def plot_yticks(self):
        yticks = get_info(self.indicator, "yticks", ())
        if yticks:
            self.ax.set_yticks(yticks)
            self.ax.grid(axis="y", which="major", linestyle="-", linewidth=2)

    def plot_oversold(self):
        oversold = get_info(self.indicator, "oversold", None)
        if oversold is not None:
            # color = self.chart.get_color("oversold", self.ax, self.indicator, fallback="fill")
            with np.errstate(invalid="ignore"):
                xv, yv = self.series_xy()
                self.ax.fill_between(
                    xv,
                    yv,
                    oversold,
                    where=(yv <= oversold),
                    interpolate=True,
                    alpha=0.5,
                )

    def plot_overbought(self):
        overbought = get_info(self.indicator, "overbought", None)
        if overbought is not None:
            # color = self.chart.get_color("overbought", self.ax, self.indicator, fallback="fill")
            with np.errstate(invalid="ignore"):
                xv, yv = self.series_xy()
                self.ax.fill_between(
                    xv,
                    yv,
                    overbought,
                    where=(yv >= overbought),
                    interpolate=True,
                    alpha=0.5,
                )

    def plot_all(self):
        name = get_name(self.indicator).lower()
        label = get_label(self.indicator)
        bands = dict()
        counter = 0

        columns = self.get_columns()

        if not columns:
            line_style = get_info(self.indicator, "line_style", "solid")

            if line_style == "bars":
                self.plot_bars(name, label=label)
            elif line_style == "area":
                self.plot_area(name, label=label)
            else:
                self.plot_line(name, style=line_style, label=label)

        for item in columns:
            if counter > 0:
                label = None

            if item in ("upperband", "lowerband", "middleband"):
                bands[item.removesuffix("band")] = item
                continue

            if item.endswith("hist"):
                self.plot_bars(item, label=label)
                continue

            self.plot_line(item, label=label)
            counter += 1

        if bands:
            self.plot_bands(**bands, label=label)
            counter += 1

        self.plot_yticks()
        self.plot_oversold()
        self.plot_overbought()

