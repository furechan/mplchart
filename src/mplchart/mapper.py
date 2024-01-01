""" date mapper """

import numpy as np
import pandas as pd

from .locator import DateIndexLocator
from .formatter import DateIndexFormatter

import warnings


class RawDateMapper:
    """RawDate mapper between date and number using matplotlib.dates"""

    def __init__(self, max_bars=None, start=None, end=None):
        if max_bars and (start or end):
            raise ValueError(
                "Cannot specify max_bars with either start or end parameters!"
            )

        if start and end and start >= end:
            raise ValueError("'start' argument must be less than 'end' argument!")

        self.max_bars = max_bars
        self.start = start
        self.end = end

    def map_date(self, date):  # needed for plot_vline
        """returns date as number/coordinate"""
        return date

    def map_dates_old(self, dates):  # legacy (was needed for locator)
        """returns date as number/coordinate"""
        warnings.warn("RsawDataManager.map_dates is legacy!")
        return dates

    def get_date_old(self, value):  # legacy (was needed for locator/formatter)
        """returns number/coordinate as date"""
        warnings.warn("RsawDataManager.get_date is legacy!")
        return value

    def slice(self, data):
        """slice data on dates"""

        if self.start or self.end:
            data = data.loc[self.start : self.end]

        if self.max_bars and len(data) > self.max_bars:
            data = data.iloc[-self.max_bars :]

        return data

    def extract_df(self, data):
        """extracts dataframe by mapping date to number/coordinate"""

        if self.start or self.end:
            data = data.loc[self.start : self.end]

        if self.max_bars and len(data) > self.max_bars:
            data = data.iloc[-self.max_bars :]

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

    index = None

    def __init__(self, index, *, max_bars=None, start=None, end=None):
        if index is None:
            raise ValueError("index is None!")

        if start and end and start >= end:
            raise ValueError("'start' argument must be less than 'end' argument!")

        self.index = index
        self.max_bars = max_bars
        self.start = start
        self.end = end

    def map_date(self, date):  # nedded for plot_vline
        """location of date in index"""

        result = self.index.get_indexer([date], method="bfill")

        return result[0]

    def slice(self, data):
        """slice data on dates"""

        if self.start or self.end:
            data = data.loc[self.start : self.end]

        if self.max_bars and len(data) > self.max_bars:
            data = data.iloc[-self.max_bars :]

        return data

    def extract_df(self, data):
        """extracts dataframe by mapping date to position/coordinate"""

        xloc = pd.Series(np.arange(len(self.index)), index=self.index)

        if self.start or self.end:
            xloc = xloc[self.start : self.end]

        if self.max_bars:
            xloc = xloc.tail(self.max_bars)

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
