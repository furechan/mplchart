""" Talib wrapper """

import warnings

from .model import Wrapper
from .utils import series_xy

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

        def get_series(name):
            if data.__class__.__name__ == "Series":
                series = data
            else:
                series = data[name]
            return series_xy(series)

        def plot_line(name, *, linestyle="-", label=None):
            xv, yv = get_series(name)
            ax.plot(xv, yv, linestyle=linestyle, label=label)

        def plot_bars(name, *, label=None):
            xv, yv = get_series(name)
            ax.bar(xv, yv, alpha=0.5, width=0.8, label=label)

        def plot_bands(upper, lower, *, label=None):
            xs, us = get_series(upper)
            xs, ls = get_series(lower)
            ax.fill_between(xs, ls, us,
                            interpolate=True, alpha=0.2,
                            label=label)

        upper, lower = None, None

        for name, flags in self.indicator.output_flags.items():
            label = repr(self) if name in ("real", "interer") else name
            for flag in flags:
                if flag == "Line":
                    plot_line(name, label=label)
                elif flag == "Dashed Line":
                    plot_line(name, linestyle="-", label=label)
                elif flag == "Histogram":
                    plot_bars(name, label=label)
                elif flag == UPPER_LIMIT:
                    upper = name
                elif flag == LOWER_LIMIT:
                    lower = name
                else:
                    warnings.warn(f"Unknown flag {flag!r}")

        if upper and lower:
            plot_bands(upper, lower, label=repr(self))
