"""technical analysis indicators"""

import numpy as np

from . import library

from .model import Indicator
from .utils import get_series, series_xy
from .colors import default_edgecolor, closest_color


class SMA(Indicator):
    """Simple Moving Average"""

    same_scale: bool = True

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_sma(series, self.period)


class EMA(Indicator):
    """Exponential Moving Average"""

    same_scale: bool = True

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_ema(series, self.period)


class WMA(Indicator):
    """Weighted Moving Average"""

    same_scale: bool = True

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_wma(series, self.period)


class HMA(Indicator):
    """Hull Moving Average"""

    same_scale: bool = True

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_hma(series, self.period)


class ROC(Indicator):
    """Rate of Change"""

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_roc(series, self.period)


class ATR(Indicator):
    """Average True Range"""

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_atr(prices, self.period)


class ATRP(Indicator):
    """Average True Range (Percent)"""

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_atr(prices, self.period, percent=True)


class SLOPE(Indicator):
    """Slope (Linear regression with time)"""

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_slope(series, self.period)


class RSI(Indicator):
    """Relative Strengh Index"""

    default_pane: str = "above"
    color: str = None

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_rsi(series, self.period)

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes("above")

        label = str(self)
        xv, yv = series_xy(data)

        color = self.color or default_edgecolor()

        ax.plot(xv, yv, label=label, color=color)

        with np.errstate(invalid="ignore"):
            ax.fill_between(xv, yv, 70, where=(yv >= 70), interpolate=True, alpha=0.5)
            ax.fill_between(xv, yv, 30, where=(yv <= 30), interpolate=True, alpha=0.5)

        ax.set_yticks([30, 50, 70])
        ax.grid(axis="y", which="major", linestyle="-", linewidth=2)

        # ax.set_yticks([30, 50, 70], minor=True)
        # ax.grid(axis="y", which="minor", linestyle=":", linewidth=2)
        # yformatter = ax.yaxis.get_major_formatter()
        # ax.yaxis.set_minor_formatter(yformatter)


class ADX(Indicator):
    """Average Directinal Index"""

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_adx(prices, self.period)

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes("below")

        label = str(self)
        xv, yv = series_xy(data)

        adxcolor = default_edgecolor()

        ax.plot(xv, yv, color=adxcolor, label=label)

        ax.set_yticks([20, 40])
        ax.grid(axis="y", which="major", linestyle="-", linewidth=2)


class DMI(Indicator):
    """Directional Movement Index"""

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_dmi(prices, self.period)

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes("below")

        label = str(self)

        adx = data.iloc[:, 0]
        pdi = data.iloc[:, 1]
        ndi = data.iloc[:, 2]

        adxcolor = default_edgecolor()
        pdicolor = closest_color("green")
        ndicolor = closest_color("red")

        xv, yv = series_xy(adx)
        ax.plot(xv, yv, color=adxcolor, label=label)

        xv, yv = series_xy(pdi)
        ax.plot(xv, yv, color=pdicolor)

        xv, yv = series_xy(ndi)
        ax.plot(xv, yv, color=ndicolor)

        ax.set_yticks([20, 40])
        ax.grid(axis="y", which="major", linestyle="-", linewidth=2)

        # ax.set_yticks([20, 40], minor=True)
        # ax.grid(axis="y", which="minor", linestyle=":", linewidth=2)
        # yformatter = ax.yaxis.get_major_formatter()
        # ax.yaxis.set_minor_formatter(yformatter)


class MACD(Indicator):
    """Moving Average Convergence Divergence"""

    def __init__(self, n1: int = 12, n2: int = 26, n3: int = 9):
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3

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

        edgecolor = default_edgecolor()

        xv, yv = series_xy(macd)
        ax.plot(xv, yv, color=edgecolor, label=label)

        xv, yv = series_xy(signal)
        ax.plot(xv, yv)

        xv, yv = series_xy(hist)
        ax.bar(xv, yv, alpha=0.5, width=0.8)


class PPO(Indicator):
    """Price Percentage Oscillator"""

    def __init__(self, n1: int = 12, n2: int = 26, n3: int = 9):
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3

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

        edgecolor = default_edgecolor()

        xv, yv = series_xy(ppo)
        ax.plot(xv, yv, color=edgecolor, label=label)

        xv, yv = series_xy(signal)
        ax.plot(xv, yv)

        xv, yv = series_xy(hist)
        ax.bar(xv, yv, alpha=0.5, width=0.8)


class BBANDS(Indicator):
    """Bollinger Bands"""

    same_scale: bool = True
    color: str = None

    def __init__(self, period: int = 20, nbdev: float = 2.0):
        self.period = period
        self.nbdev = nbdev

    def __call__(self, prices):
        return library.calc_bbands(prices, self.period, self.nbdev)

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes("samex")

        label = str(self)

        upper = data.iloc[:, 0]
        middle = data.iloc[:, 1]
        lower = data.iloc[:, 2]

        color = self.color

        xs, ms = series_xy(middle)
        res = ax.plot(xs, ms, color=color, linestyle="dashed", label=label)

        color = res[-1].get_color()  # uodate color from last plot

        xs, hs = series_xy(upper)
        ax.plot(xs, hs, color=color, linestyle="dotted")

        xs, ls = series_xy(lower)
        ax.plot(xs, ls, color=color, linestyle="dotted")

        ax.fill_between(xs, ls, hs, color=color, interpolate=True, alpha=0.2)


__all__ = [k for k in dir() if k.isupper()]
