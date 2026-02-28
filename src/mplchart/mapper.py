"""date mapper"""

import numpy as np
import pandas as pd

from .locators import DTArrayLocator
from .formatters import DTArrayFormatter



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

    def slice(self, data):
        """re-index and slice data"""

        if self.start or self.end:
            data = data.loc[self.start : self.end]

        return data


    def map_date(self, date):  # needed for plot_vline
        return date

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


    def config_axes(self, ax):
        """set locator and formatter"""

        dtarray = self.index.tz_localize(None)
        locator = DTArrayLocator(dtarray)
        formatter =  DTArrayFormatter(dtarray)

        if locator:
            ax.xaxis.set_major_locator(locator)

        if formatter:
            ax.xaxis.set_major_formatter(formatter)
