""" ticker formatters """

import warnings
import numpy as np

import matplotlib.ticker as mticker

from .datetimes import date_labels

# TODO remove DateIndexFormatter


class DateIndexFormatter(mticker.Formatter):
    """Formatter based on a pandas DateTimeIndex (pandas based)"""

    def __init__(self, index, *, fmt="%Y-%m-%d"):
        warnings.warn("DateIndexFormatter is deprecated, use DTArrayFormatter instead",
                      DeprecationWarning, stacklevel=2)

        if index is None:
            raise ValueError("index is None!")
        self.index = index
        self.fmt = fmt

    def __call__(self, value, pos=None):
        return self.format_data(value)

    def format_data(self, value):
        """date label"""
        size = len(self.index)
        idx = np.floor(value).astype(int).clip(0, size - 1)
        date = self.index[idx]
        return date.strftime(self.fmt)

    def format_ticks(self, values):
        """date labels"""
        size = len(self.index)
        idx = np.floor(values).astype(int).clip(0, size - 1)
        dates = self.index[idx]
        return date_labels(dates)


class DTArrayFormatter(mticker.Formatter):
    """Formatter for a numpy array of datetime (numpy based)"""

    def __init__(self, dtarray, *, fmt="%Y-%m-%d"):
        if hasattr(dtarray, "tz_localize"):
            dtarray = dtarray.tz_localize(None)

        dtarray = np.asarray(dtarray, 'datetime64[s]')
        self.dtarray = dtarray
        self.fmt = fmt

    def __call__(self, value, pos=None):
        return self.format_data(value)

    def format_data(self, value):
        """date label"""
        size = len(self.dtarray)
        idx = np.floor(value).astype(int).clip(0, size - 1)
        date = self.dtarray[idx]
        return date.astype('O').strftime(self.fmt)

    def format_ticks(self, values):
        """date labels"""
        size = len(self.dtarray)
        idx = np.floor(values).astype(int).clip(0, size - 1)
        dates = self.dtarray[idx]
        return date_labels(dates)
