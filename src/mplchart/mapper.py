"""date mapper"""

import numpy as np
import pandas as pd

import warnings

from .locator import DateIndexLocator
from .formatter import DateIndexFormatter


class RawDateMapper:
    """Raw Date Mapper (no mapping, just slices dates)"""

    def __init__(self, index, max_bars=None, start=None, end=None):
        if start or end:
            locs = index.tz_localize(None).slice_indexer(start=start, end=end)
            index = index[locs]

        if max_bars and max_bars > 0:
            index = index[-max_bars:]

        self.start = index[0]
        self.end = index[-1]

    def extract_df(self, data):
        """extract data by mapping date to positions (deprecated)"""

        warnings.warn("extract_df is deprecated. Use slice instead!", DeprecationWarning, stacklevel=2)

        if self.start or self.end:
            data = data.loc[self.start : self.end]

        return data

    def reindex(self, data):
        """re-index data by mapping dates to positions"""

        warnings.warn("reindex is deprecated. Use slice instead!", DeprecationWarning, stacklevel=2)

        if self.start or self.end:
            data = data.loc[self.start : self.end]

        return data

    def slice(self, data):
        """re-index and slice data"""

        if self.start or self.end:
            data = data.loc[self.start : self.end]

        return data


    def map_date(self, date):  # needed for plot_vline
        return date

    def get_locator(self):
        return None

    def get_formatter(self):
        return None

    def config_axes(self, ax):
        pass


class DateIndexMapper:
    """Date Index Mapper maps dates to integers"""

    def __init__(self, index, *, max_bars=None, start=None, end=None):
        if start or end:
            locs = index.tz_localize(None).slice_indexer(start=start, end=end)
            index = index[locs]

        if max_bars and max_bars > 0:
            index = index[-max_bars:]

        self.index = index

    def extract_df(self, data):
        """extract data by mapping date to positions (deprecated)"""

        warnings.warn("extract_df is deprecated. Use slice instead!", DeprecationWarning, stacklevel=2)

        xloc = pd.Series(np.arange(len(self.index)), index=self.index)

        xloc, data = xloc.align(data, join="inner")

        data = data.set_axis(xloc)

        return data


    def reindex(self, data):
        """re-index data by mapping dates to positions"""

        warnings.warn("reindex is deprecated. Use slice instead!", DeprecationWarning, stacklevel=2)

        xloc = pd.Series(np.arange(len(self.index)), index=self.index, name='xloc')

        xloc, data = xloc.align(data, join="inner")

        data = data.set_axis(xloc)

        return data


    def slice(self, data):
        """re-index and slice data by mapping dates to positions"""

        xloc = pd.Series(np.arange(len(self.index)), index=self.index, name='xloc')

        xloc, data = xloc.align(data, join="inner")

        data = data.set_axis(xloc)

        return data


    def map_date(self, date):  # nedded for plot_vline
        """location of date in index"""

        result = self.index.get_indexer([date], method="bfill")

        return result[0]

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
