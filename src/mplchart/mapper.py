"""date mapper"""

import numpy as np
import pandas as pd

from .locator import DateIndexLocator
from .formatter import DateIndexFormatter


class RawDateMapper:
    """RawDate mapper between date and number using matplotlib.dates"""

    def __init__(self, index, max_bars=None, start=None, end=None):
        if start or end:
            locs = index.slice_indexer(start=start, end=end)
            index = index[locs]

        if max_bars > 0:
            index = index[-max_bars:]

        self.start = index[0]
        self.end = index[-1]

    def map_date(self, date):  # needed for plot_vline
        """returns date as number/coordinate"""
        return date

    def extract_df(self, data):
        """extracts dataframe by mapping date to number/coordinate"""

        if self.start or self.end:
            data = data.loc[self.start:self.end]

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
        if start or end:
            locs = index.slice_indexer(start=start, end=end)
            index = index[locs]

        if max_bars > 0:
            index = index[-max_bars:]

        self.index = index

    def map_date(self, date):  # nedded for plot_vline
        """location of date in index"""

        result = self.index.get_indexer([date], method="bfill")

        return result[0]

    def extract_df(self, data):
        """extracts dataframe by mapping date to position/coordinate"""

        xloc = pd.Series(np.arange(len(self.index)), index=self.index)

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
