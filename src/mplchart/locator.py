""" ticker locators """

import math
import logging
import numpy as np
import pandas as pd

import matplotlib.ticker as mticker

from functools import lru_cache

logger = logging.getLogger(__name__)

MAX_TICKS = 18

FREQ_VALUES = {
    '1min': 1 / 1400,
    '2min': 2 / 1440,
    '5min': 5 / 1440,
    '10min': 10 / 1440,
    '20min': 20 / 1440,
    '30min': 30 / 1440,
    '1h': 1 / 24,
    '2h': 2 / 24,
    'D': 1,
    'W': 7,
    '2W': 14,
    'MS': 30,
    'QS': 90,
    'YS': 360,
    '2YS': 720,
    '5YS': 1800,
    '10YS': 3600
}


class DateIndexLocator(mticker.Locator):
    """Locator based on a pandas DateTimeIndex"""

    def __init__(self, index):
        if index is None:
            raise ValueError("Index is None!")

        self.index = index
        self.tick_values = lru_cache(self.tick_values)

    def __call__(self):
        vmin, vmax = self.axis.get_view_interval()
        max_ticks = self.axis.get_tick_space()

        if max_ticks > MAX_TICKS:
            max_ticks = MAX_TICKS

        return self.tick_values(vmin, vmax, max_ticks=max_ticks)

    def tick_values(self, vmin, vmax, max_ticks=10):
        logger.debug("tick_values %r, %r, %r", vmin, vmax, max_ticks)

        if math.isinf(vmin) or math.isinf(vmax):
            return []

        size = len(self.index)
        irng = np.round([vmin, vmax]).astype(int).clip(0, size - 1)
        start, end = self.index[irng]
        interval = (end - start) / pd.Timedelta(days=1) / max_ticks
        freqs = [k for k, v in FREQ_VALUES.items() if v >= interval] or ['10YE']

        for freq in freqs:
            if freq.endswith(("min", "h", "D")):
                ts1 = start.ceil(freq)
                ts2 = end.floor(freq)
                if ts2 > ts1:
                    start, end = ts1, ts2

            logger.debug("date_range %r", freq)
            dates = pd.date_range(start=start, end=end, freq=freq)

            if len(dates) <= max_ticks:
                break

        tick_values = self.index.get_indexer(dates, method="bfill")
        tick_values = np.unique(tick_values)

        return self.raise_if_exceeds(tick_values)
