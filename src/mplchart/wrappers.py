"""rendering wrappers"""

import warnings
import numpy as np
import matplotlib.pyplot as plt

from functools import singledispatch

from .model import Wrapper
from .utils import get_name, get_label, get_info


@singledispatch
def get_wrapper(indicator):
    """create rendering wrapper for indicator"""

    if hasattr(indicator, "plot_handler"):
        return None

    return AutoWrapper(indicator)


class AutoWrapper(Wrapper):
    def __init__(self, indicator):
        self.indicator = indicator

    def __call__(self, data):
        warnings.warn("Wrapper used as callable!", DeprecationWarning, stacklevel=2)
        return self.indicator(data)

    def get_axes(self, chart):
        target = chart.get_target(self.indicator)
        return chart.get_axes(target)

    def next_line_color(self, ax):
        handles, _ = ax.get_legend_handles_labels()
        if len(handles):
            return ax._get_lines.get_next_color()
        else:
            return plt.rcParams["text.color"]

    def next_fill_color(self, ax):
        return ax._get_patches_for_fill.get_next_color()

    def get_columns(self, data):
        if data.__class__.__name__ == "Series":
            name = get_name(self.indicator)
            return [name.lower()]

        return list(data.columns)

    def series_xy(self, data, item=None):   # ignore item for series !!!
        """split data into x, y arrays"""
        if data.__class__.__name__ == "Series":
            series = data
        elif item is not None:
            series = data[item]
        else:
            series = data.iloc[:, 0]
        return series.index.values, series.values

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            ax = self.get_axes(chart)

        counter = 0
        bands = dict()
        label = get_label(self.indicator)

        for item in self.get_columns(data):
            if counter > 0:
                label = None

            if item.endswith("band"):
                bands[item.removesuffix("band")] = item
                continue

            if item.endswith("hist"):
                color = chart.get_color(item, ax, self.indicator, fallback="fill")
                xv, yv = self.series_xy(data, item)
                ax.bar(xv, yv, color=color, alpha=0.5, width=0.8, label=label)
                counter += 1
                continue

            color = chart.get_color(item, ax, self.indicator, fallback="line")
            xv, yv = self.series_xy(data, item)
            ax.plot(xv, yv, label=label, color=color)
            counter += 1

        if bands:
            upperband = bands["upper"]
            lowerband = bands["lower"]
            middleband = bands["middle"]

            name = get_name(self.indicator).lower()
            color = chart.get_color(name, ax, self.indicator, fallback="line")

            xv, mv = self.series_xy(data, middleband)
            xv, lv = self.series_xy(data, lowerband)
            xv, uv = self.series_xy(data, upperband)

            ax.plot(xv, mv, color=color, linestyle="dashed")
            ax.plot(xv, lv, color=color, linestyle="dotted")
            ax.plot(xv, uv, color=color, linestyle="dotted")
            ax.fill_between(
                xv, lv, uv, color=color, interpolate=True, alpha=0.2, label=label
            )
            counter += 1

        yticks = get_info(self.indicator, "yticks", ())
        if yticks:
            ax.set_yticks(yticks)
            ax.grid(axis="y", which="major", linestyle="-", linewidth=2)

        oversold = get_info(self.indicator, "oversold", None)
        if oversold is not None:
            color = chart.get_color("oversold", ax, self.indicator, fallback="fill")
            with np.errstate(invalid="ignore"):
                xv, yv = self.series_xy(data)
                ax.fill_between(
                    xv,
                    yv,
                    oversold,
                    where=(yv <= oversold),
                    interpolate=True,
                    alpha=0.5,
                )

        overbought = get_info(self.indicator, "overbought", None)
        if overbought is not None:
            color = chart.get_color("overbought", ax, self.indicator, fallback="fill")
            with np.errstate(invalid="ignore"):
                xv, yv = self.series_xy(data)
                ax.fill_between(
                    xv,
                    yv,
                    overbought,
                    where=(yv >= overbought),
                    interpolate=True,
                    alpha=0.5,
                )
