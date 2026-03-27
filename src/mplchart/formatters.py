""" ticker formatters """

import numpy as np

import matplotlib.ticker as mticker

from .datetimes import date_labels


class DTArrayFormatter(mticker.Formatter):
    """Formatter for a numpy array of datetime (numpy based)"""

    def __init__(self, dtarray, *, fmt="%Y-%m-%d"):
        if hasattr(dtarray, "tz_localize"):
            dtarray = dtarray.tz_localize(None)

        dtarray = np.asarray(dtarray, 'datetime64[s]')
        self.dtarray = dtarray
        self.fmt = fmt

    def __call__(self, x: float, pos: int | None = None) -> str:
        return self.format_data(x)

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
