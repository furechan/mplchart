""" rendering wrappers """

import numpy as np

from .utils import series_xy

from .extalib import talib_function_check, talib_function_name

__all__ = ()


def get_wrapper(indicator):
    """ gets the rendering wrapper for given indicator """

    if talib_function_check(indicator):
        name = talib_function_name(indicator)
    elif hasattr(indicator, '__name__'):
        name = indicator.__name__
    else:
        name = indicator.__class__.__name__

    wrapper = globals().get(name.upper())

    if wrapper is not None:
        return wrapper(indicator)


class Wrapper:
    """ Indicator Wrapper """

    indicator = None

    def __init__(self, indicator):
        self.indicator = indicator

    def check_result(self, data):
        return True

    def plot_result(self, data, chart, ax=None):
        pass


class LinePlot(Wrapper):
    """ LinePlot Wrapper """

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            ax = chart.new_axes()

        label = chart.get_label(self.indicator)
        xv, yv = series_xy(data)

        ax.plot(xv, yv, label=label)


class RSI(Wrapper):
    """ Relative Strendgth Index Wrapper """

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes('above')

        label = chart.get_label(self.indicator)
        xv, yv = series_xy(data)

        ax.plot(xv, yv, label=label, color='k')

        with np.errstate(invalid='ignore'):
            ax.fill_between(xv, yv, 70, where=(yv >= 70), interpolate=True, alpha=0.5)
            ax.fill_between(xv, yv, 30, where=(yv <= 30), interpolate=True, alpha=0.5)

        ax.set_yticks([30, 50, 70])


class PSAR(Wrapper):
    """ PSAR WRapper """

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes('samex')

        xv, yv = series_xy(data)

        ax.scatter(xv, yv, alpha=0.5, marker=".")


class VOLUME(Wrapper):
    """ VOLUME Wrapper """

    def plot_result(self, data, chart, ax=None):

        if ax is None:
            ax = chart.get_axes('twinx')

        index = data.index
        volume = data['volume']

        if 'change' in data:
            change = data['change']
            color = np.where(change < 0, 'red', 'grey')
        else:
            color = 'grey'

        if ax._label == 'twinx':
            vmax = volume.max()
            ax.set_ylim(0.0, vmax * 4.0)
            ax.yaxis.set_visible(False)

        ax.bar(index, volume, width=1.0, alpha=0.3, zorder=0, color=color)

        if 'average' in data:
            average = data['average']
            ax.plot(index, average, linewidth=0.7, color='grey')


class MACD(Wrapper):
    """ MACD Wrapper """

    def check_result(self, data):
        return data.ndim == 2 and data.shape[1] == 3

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes('below')

        label = chart.get_label(self.indicator)

        macd = data.iloc[:, 0]
        signal = data.iloc[:, 1]
        dist = data.iloc[:, 2] * 2.5

        xv, yv = series_xy(macd)
        ax.plot(xv, yv, color='k', label=label)

        xv, yv = series_xy(signal)
        ax.plot(xv, yv)

        xv, yv = series_xy(dist)
        ax.bar(xv, yv, alpha=0.5, width=0.8)


class BBANDS(Wrapper):
    """ BBANDS Wrapper"""

    def check_result(self, data):
        print("check_data", data.ndim, data.shape)
        return data.ndim == 2 and data.shape[1] == 3

    def plot_result(self, data, chart, ax=None):
        if ax is None:
            ax = chart.get_axes('samex')

        label = chart.get_label(self.indicator)

        upper = data.iloc[:, 0]
        middle = data.iloc[:, 1]
        lower = data.iloc[:, 2]

        xs, ms = series_xy(middle)
        ax.plot(xs, ms, color='blue', label=label)

        xs, hs = series_xy(upper)
        ax.plot(xs, hs, color='orange')

        xs, ls = series_xy(lower)
        ax.plot(xs, ls, color='orange')

        ax.fill_between(xs, ls, hs, color='orange', interpolate=True, alpha=0.3)
