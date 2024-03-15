""" date mapper """

import numpy as np
import pandas as pd

from .locator import DateIndexLocator
from .formatter import DateIndexFormatter


def get_boundaries(index, max_bars=None, start=None, end=None):
    if index is None:
        raise ValueError("Index is None!")

    if max_bars and (start or end):
        raise ValueError(
            "Cannot specify `max_bars` together with `start` or `end`!"
        )

    if start and end and start >= end:
        raise ValueError("Argument `start` value must be less than `end` value!")

    if max_bars and len(index) > max_bars:
        start = index[-max_bars]

    if start is None and len(index):
        start = index[0]

    if end is None and len(index):
        end = index[-1]

    return start, end


class RawDateMapper:
    """RawDate mapper between date and number using matplotlib.dates"""

    def __init__(self, index, max_bars=None, start=None, end=None):
        start, end = get_boundaries(index, max_bars=max_bars, start=start, end=end)

        self.start = start
        self.end = end

    def map_date(self, date):  # needed for plot_vline
        """returns date as number/coordinate"""
        return date

    def slice(self, data):
        """slice data on dates"""

        if self.start or self.end:
            data = data.loc[self.start: self.end]

        return data

    def extract_df(self, data):
        """extracts dataframe by mapping date to number/coordinate"""

        if self.start or self.end:
            data = data.loc[self.start: self.end]

        return data

    def get_locator(self):
        """no locator needed"""
        return None

    def get_formatter(self):
        """no formatter needed"""
        return None

    def config_axes(self, ax):
        """no config needed"""
        pass


class DateIndexMapper:
    """DateIndex mapper between date and position/coordinate"""

    def __init__(self, index, *, max_bars=None, start=None, end=None):
        start, end = get_boundaries(index, max_bars=max_bars, start=start, end=end)

        self.index = index
        self.start = start
        self.end = end

    def map_date(self, date):  # nedded for plot_vline
        """location of date in index"""

        result = self.index.get_indexer([date], method="bfill")

        return result[0]

    def slice(self, data):
        """slice data on dates"""

        if self.start or self.end:
            data = data.loc[self.start: self.end]

        return data

    def extract_df(self, data):
        """extracts dataframe by mapping date to position/coordinate"""

        xloc = pd.Series(np.arange(len(self.index)), index=self.index)

        if self.start or self.end:
            xloc = xloc[self.start: self.end]

        xloc, data = xloc.align(data, join="inner")

        return data.set_axis(xloc)

    def get_locator(self):
        """locator for this mapper"""

        return DateIndexLocator(index=self.index)

    def get_formatter(self):
        """formatter for this mapper"""

        return DateIndexFormatter(index=self.index)

    def config_axes(self, ax):
        """set locator and formatter"""
        locator = self.get_locator()
        formatter = self.get_formatter()

        if locator:
            ax.xaxis.set_major_locator(locator)

        if formatter:
            ax.xaxis.set_major_formatter(formatter)
