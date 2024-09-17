"""Talib wrapper"""

import warnings

from .model import Wrapper


SOLID_LINE = "Line"
HISTOGRAM = "Histogram"
DASHED_LINE = "Dashed Line"
SAME_SCALE = "Output scale same as input"
UPPER_LIMIT = "Values represent an upper limit"
LOWER_LIMIT = "Values represent a lower limit"


# TODO Remove talib_function_check


def talib_function_check(indicator):
    warnings.warn(
        "talib_function_check is deprecated", DeprecationWarning, stacklevel=2
    )
    return hasattr(indicator, "func_object")


class TalibWrapper(Wrapper):
    def __init__(self, indicator):
        self.indicator = indicator

    @classmethod
    def check_indicator(cls, indicator):
        return hasattr(indicator, "func_object")

    @property
    def same_scale(self):
        flags = self.indicator.function_flags or ()
        return SAME_SCALE in flags

    def get_axes(self, chart):
        target = "samex" if self.same_scale else "below"
        return chart.get_axes(target)

    def get_label(self):
        name = self.indicator.info.get("name")
        params = [repr(v) for v in self.indicator.parameters.values()]
        return name + "(" + ", ".join(params) + ")"

    def series_data(self, data, name):
        if data.__class__.__name__ == "Series":
            series = data
        else:
            series = data[name]
        return series.index.values, series.values

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            ax = self.get_axes(chart)

        upper_limit, lower_limit = None, None

        for name, flags in self.indicator.output_flags.items():
            label = self.get_label() if name in ("real", "interer") else name

            for flag in flags:
                if flag == HISTOGRAM:
                    xv, yv = self.series_data(data, name)
                    ax.bar(xv, yv, alpha=0.5, width=0.8, label=label)
                    continue

                linestyle = None

                if flag == SOLID_LINE:
                    linestyle = "-"
                elif flag == DASHED_LINE:
                    linestyle = "--"
                elif flag in UPPER_LIMIT:
                    upper_limit = name
                    linestyle = "-."
                elif flag == LOWER_LIMIT:
                    lower_limit = name
                    linestyle = "-."
                else:
                    warnings.warn(f"Unknown flag {flag!r}")

                xv, yv = self.series_data(data, name)
                ax.plot(xv, yv, linestyle=linestyle, label=label)

        if upper_limit and lower_limit:
            xs, us = self.series_data(data, upper_limit)
            xs, ls = self.series_data(data, lower_limit)
            ax.fill_between(xs, ls, us, interpolate=True, alpha=0.2)
