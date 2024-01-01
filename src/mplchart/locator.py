""" ticker locators """

import math
import matplotlib.ticker as mticker

from functools import lru_cache

from .datetime import date_ticks

VERBOSE = False


class DateIndexLocator(mticker.Locator):
    """Locator based on a pandas DateTimeIndex"""

    def __init__(self, index, *, verbose=VERBOSE):
        if index is None:
            raise ValueError("Index is None!")

        self.index = index
        self.verbose = verbose
        self.tick_values = lru_cache(self.tick_values)

    def __call__(self):
        vmin, vmax = self.axis.get_view_interval()
        max_ticks = self.axis.get_tick_space()

        return self.tick_values(vmin, vmax, max_ticks=max_ticks)

    def get_date(self, value, clip=False):
        """returns date from position (used in tick_values)"""

        idx = int(round(value))

        size = len(self.index)

        if idx < 0:
            if clip:
                idx = 0
            else:
                return None

        if idx >= size:
            if clip:
                idx = size - 1
            else:
                return None

        return self.index[idx]

    def map_dates(self, dates):
        """returns location of date in index (used in tick_values)"""

        return self.index.get_indexer(dates, method="bfill")

    def tick_values(self, vmin, vmax, max_ticks=10):
        if self.verbose:
            print("tick_values", vmin, vmax, max_ticks)

        if math.isinf(vmin) or math.isinf(vmax):
            return []

        start = self.get_date(vmin, clip=True)
        end = self.get_date(vmax, clip=True)

        dates = date_ticks(start=start, end=end, max_ticks=max_ticks)

        tick_values = self.map_dates(dates)

        return self.raise_if_exceeds(tick_values)
