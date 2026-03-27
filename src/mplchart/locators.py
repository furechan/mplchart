""" ticker locators """

import math
import logging
import numpy as np

import matplotlib.ticker as mticker

from typing import Callable, Any
from functools import lru_cache

from .datetimes import date_ticks

logger = logging.getLogger(__name__)

MAX_TICKS = 12



class DTArrayLocator(mticker.Locator):
    """Locator based on a numpy array of datetimes"""

    _tick_values: Callable[..., Any]

    def __init__(self, dtarray):
        if hasattr(dtarray, "tz_localize"):
            dtarray = dtarray.tz_localize(None)

        dtarray = np.asarray(dtarray, 'datetime64[s]')
        self.dtarray = dtarray
        self._tick_values = lru_cache(self._compute_ticks)

    def __call__(self):
        if self.axis is None:
            return []

        vmin, vmax = self.axis.get_view_interval()
        max_ticks = self.axis.get_tick_space()

        if max_ticks > MAX_TICKS:
            max_ticks = MAX_TICKS

        return self._tick_values(vmin, vmax, max_ticks=max_ticks)

    def tick_values(self, vmin: float, vmax: float):
        return self._tick_values(vmin, vmax, max_ticks=MAX_TICKS)

    def _compute_ticks(self, vmin, vmax, max_ticks=10):
        logger.debug("tick_values %r, %r, %r", vmin, vmax, max_ticks)

        if math.isinf(vmin) or math.isinf(vmax):
            return []

        size = len(self.dtarray)
        vmin, vmax = np.round([vmin, vmax]).astype(int).clip(0, size - 1)
        dates = self.dtarray[vmin:vmax+1]

        return date_ticks(dates, max_ticks)
