""" technical analysis indicators """

import numpy as np

from dataclasses import dataclass

from typing import ClassVar

from inspect import Signature, Parameter

from . import library

from .library import get_series
from .utils import series_xy


def auto_label(self):
    cname = self.__class__.__qualname__
    signature = Signature.from_callable(self.__init__)
    args, keyword_only = [], False

    for p in signature.parameters.values():
        v = getattr(self, p.name, p.default)

        if p.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
            raise ValueError(f"Unsupported parameter type {p.kind}")

        if p.kind == Parameter.KEYWORD_ONLY:
            keyword_only = True
        elif isinstance(p.default, (type(None), str, bool)):
            keyword_only = True

        if v == p.default:
            # skip argument if not equal to default
            if keyword_only or not isinstance(v, (int, float)):
                keyword_only = True
                continue

        if keyword_only:
            args.append(f"{p.name}={v!r}")
        else:
            args.append(f"{v!r}")

    args = ", ".join(args)

    return f"{cname}({args})"


class Indicator:
    """Injects a basic __repr__ based on __init__ signature"""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__str__ = auto_label


@dataclass
class SMA(Indicator):
    """Simple Moving Average"""

    period: int = 20

    same_scale: ClassVar[bool] = True

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_sma(series, self.period)


@dataclass
class EMA(Indicator):
    """Exponential Moving Average"""

    period: int = 20

    same_scale: ClassVar[bool] = True

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_ema(series, self.period)


@dataclass
class ROC(Indicator):
    """Rate of Change"""

    period: int = 20

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_roc(series, self.period)


@dataclass
class RSI(Indicator):
    """Relative Strengh Index"""

    period: int = 14

    default_pane: ClassVar[str] = "above"
    COLOR: ClassVar[str] = "black"

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_rsi(series, self.period)

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes("above")

        label = str(self)
        xv, yv = series_xy(data)

        color = chart.get_setting("rsi", "color", self.COLOR)

        ax.plot(xv, yv, label=label, color=color)

        with np.errstate(invalid="ignore"):
            ax.fill_between(xv, yv, 70, where=(yv >= 70), interpolate=True, alpha=0.5)
            ax.fill_between(xv, yv, 30, where=(yv <= 30), interpolate=True, alpha=0.5)

        ax.set_yticks([30, 70])
        ax.set_yticks([30, 50, 70], minor=True)
        ax.grid(axis="y", which="major", linestyle="-", linewidth=2)
        ax.grid(axis="y", which="minor", linestyle=":", linewidth=2)

        yformatter = ax.yaxis.get_major_formatter()
        ax.yaxis.set_minor_formatter(yformatter)


@dataclass
class ATR(Indicator):
    """Average True Range"""

    period: int = 14

    def __call__(self, prices):
        return library.calc_atr(prices, self.period)


@dataclass
class ADX(Indicator):
    """Average Directional Index"""

    period: int = 14

    def __call__(self, prices):
        return library.calc_adx(prices, self.period)

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes("below")

        label = str(self)

        adx = data.iloc[:, 0]
        pdi = data.iloc[:, 1]
        mdi = data.iloc[:, 2]

        xv, yv = series_xy(adx)
        ax.plot(xv, yv, color="k", label=label)

        xv, yv = series_xy(pdi)
        ax.plot(xv, yv, color="g")

        xv, yv = series_xy(mdi)
        ax.plot(xv, yv, color="r")

        ax.set_yticks([20])
        ax.set_yticks([20, 40], minor=True)
        ax.grid(axis="y", which="major", linestyle="-", linewidth=2)
        ax.grid(axis="y", which="minor", linestyle=":", linewidth=2)

        yformatter = ax.yaxis.get_major_formatter()
        ax.yaxis.set_minor_formatter(yformatter)


@dataclass
class MACD(Indicator):
    """Moving Average Convergence Divergence"""

    n1: int = 12
    n2: int = 26
    n3: int = 9

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_macd(series, self.n1, self.n2, self.n3)

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes("below")

        label = str(self)

        macd = data.iloc[:, 0]
        signal = data.iloc[:, 1]
        hist = data.iloc[:, 2] * 2.0

        xv, yv = series_xy(macd)
        ax.plot(xv, yv, color="k", label=label)

        xv, yv = series_xy(signal)
        ax.plot(xv, yv)

        xv, yv = series_xy(hist)
        ax.bar(xv, yv, alpha=0.5, width=0.8)


@dataclass
class PPO(Indicator):
    """Price Percentage Oscillator"""

    n1: int = 12
    n2: int = 26
    n3: int = 9

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_ppo(series, self.n1, self.n2, self.n3)

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes("below")

        label = str(self)

        ppo = data.iloc[:, 0]
        signal = data.iloc[:, 1]
        hist = data.iloc[:, 2] * 2.0

        xv, yv = series_xy(ppo)
        ax.plot(xv, yv, color="k", label=label)

        xv, yv = series_xy(signal)
        ax.plot(xv, yv)

        xv, yv = series_xy(hist)
        ax.bar(xv, yv, alpha=0.5, width=0.8)


@dataclass
class SLOPE(Indicator):
    """Slope (Linear regression with time)"""

    period: int = 20

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_slope(series, self.period)


@dataclass
class BBANDS(Indicator):
    """Bollinger Bands"""

    period: int = 20
    nbdev: float = 2.0

    same_scale: ClassVar[bool] = True
    COLOR: ClassVar[str] = "orange"

    def __call__(self, prices):
        return library.calc_bbands(prices, self.period, self.nbdev)

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes("samex")

        label = str(self)

        upper = data.iloc[:, 0]
        middle = data.iloc[:, 1]
        lower = data.iloc[:, 2]

        color = self.COLOR

        xs, ms = series_xy(middle)
        ax.plot(xs, ms, color=color, linestyle="dashed", label=label)

        xs, hs = series_xy(upper)
        ax.plot(xs, hs, color=color, linestyle="dotted")

        xs, ls = series_xy(lower)
        ax.plot(xs, ls, color=color, linestyle="dotted")

        ax.fill_between(xs, ls, hs, color=color, interpolate=True, alpha=0.2)


__all__ = [k for k in dir() if k.isupper()]
