""" technical analysis indicators """

import numpy as np

from . import library

from .model import Indicator
from .utils import get_series, series_xy


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


class RSI(Indicator):
    """Relative Strengh Index"""

    default_pane: str = "above"
    color: str = "black"

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

        color = self.color

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


class ATR(Indicator):
    """Average True Range"""

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_atr(prices, self.period)


class ADX(Indicator):
    """Average Directional Index"""

    def __init__(self, period: int = 14):
        self.period = period

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

        xv, yv = series_xy(macd)
        ax.plot(xv, yv, color="k", label=label)

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

        xv, yv = series_xy(ppo)
        ax.plot(xv, yv, color="k", label=label)

        xv, yv = series_xy(signal)
        ax.plot(xv, yv)

        xv, yv = series_xy(hist)
        ax.bar(xv, yv, alpha=0.5, width=0.8)


class SLOPE(Indicator):
    """Slope (Linear regression with time)"""

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_slope(series, self.period)


class BBANDS(Indicator):
    """Bollinger Bands"""

    same_scale: bool = True
    color: str = "orange"

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
        ax.plot(xs, ms, color=color, linestyle="dashed", label=label)

        xs, hs = series_xy(upper)
        ax.plot(xs, hs, color=color, linestyle="dotted")

        xs, ls = series_xy(lower)
        ax.plot(xs, ls, color=color, linestyle="dotted")

        ax.fill_between(xs, ls, hs, color=color, interpolate=True, alpha=0.2)


__all__ = [k for k in dir() if k.isupper()]
