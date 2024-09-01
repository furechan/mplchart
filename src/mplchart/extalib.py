""" Talib wrapper """

import warnings

from .model import Wrapper
from .utils import series_xy

SOLID_LINE = "Line"
HISTOGRAM = "Histogram"
DASHED_LINE = "Dashed Line"
SAME_SCALE = "Output scale same as input"
UPPER_LIMIT = "Values represent an upper limit"
LOWER_LIMIT = "Values represent a lower limit"


def talib_function_check(indicator):
    return hasattr(indicator, "func_object")


def talib_function_name(indicator):
    warnings.warn("talib_function_name is deprecated!", DeprecationWarning)
    return indicator.info.get("name")


def talib_function_repr(indicator):
    warnings.warn("talib_function_repr is deprecated!", DeprecationWarning)
    name = indicator.info.get("name")
    params = [repr(v) for v in indicator.parameters.values()]
    return name + "(" + ", ".join(params) + ")"


def talib_same_scale(indicator):
    warnings.warn("talib_same_scale is deprecated!", DeprecationWarning)
    flags = indicator.function_flags
    return flags and SAME_SCALE in flags


class TalibWrapper(Wrapper):

    def __repr__(self):
        name = self.indicator.info.get("name")
        params = [repr(v) for v in self.indicator.parameters.values()]
        return name + "(" + ", ".join(params) + ")"

    @property
    def same_scale(self):
        flags = self.indicator.function_flags
        return flags and SAME_SCALE in flags

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            target = "samex" if self.same_scale else "below"
            ax = chart.get_axes(target)

        def _series_data(name):
            if data.__class__.__name__ == "Series":
                series = data
            else:
                series = data[name]
            return series_xy(series)

        upper_limit, lower_limit = None, None

        for name, flags in self.indicator.output_flags.items():
            label = repr(self) if name in ("real", "interer") else name
            for flag in flags:
                if flag == HISTOGRAM:
                    xv, yv = _series_data(name)
                    ax.bar(xv, yv, alpha=0.5, width=0.8, label=label)
                    continue

                linestyle = None

                if flag == SOLID_LINE:
                    linestyle = "-"
                elif flag == DASHED_LINE:
                    linestyle = "--"
                elif flag == UPPER_LIMIT:
                    upper_limit = name
                    linestyle = "-."
                elif flag == LOWER_LIMIT:
                    lower_limit = name
                    linestyle = "-."
                else:
                    warnings.warn(f"Unknown flag {flag!r}")

                xv, yv = _series_data(name)
                ax.plot(xv, yv, linestyle=linestyle, label=label)

        if upper_limit and lower_limit:
            xs, us = _series_data(upper_limit)
            xs, ls = _series_data(lower_limit)
            ax.fill_between(xs, ls, us,
                            interpolate=True,
                            alpha=0.2)
