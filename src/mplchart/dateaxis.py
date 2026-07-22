"""Date x-axis machinery — locator, formatter, and axis wiring.

Everything needed to render a rownum-coordinate x-axis with date labels:
``DTArrayLocator`` / ``DTArrayFormatter`` map tick positions back to dates
through a datetime array, and ``config_date_axis`` installs them on an axes.
Imports matplotlib and numpy only — no chart or data-plane dependencies.
"""

import math
import logging
import numpy as np

import matplotlib.ticker as mticker

from typing import Callable, Any
from functools import lru_cache

from .datetimes import date_ticks, date_labels

logger = logging.getLogger(__name__)

MAX_DATE_TICKS = 12


def as_dtarray(dates) -> np.ndarray:
    """Coerce a native datetime array-like to a tz-naive datetime64[s] array.

    Accepts a DatetimeIndex, polars Series, or numpy array; a no-op when
    already coerced.
    """
    if hasattr(dates, "tz_localize"):
        dates = dates.tz_localize(None)
    return np.asarray(dates, 'datetime64[s]')


class DTArrayLocator(mticker.Locator):
    """Locator based on a numpy array of datetimes"""

    _tick_values: Callable[..., Any]

    def __init__(self, dtarray):
        self.dtarray = as_dtarray(dtarray)
        self._tick_values = lru_cache(self._compute_ticks)

    def __call__(self):
        if self.axis is None:
            return []

        vmin, vmax = self.axis.get_view_interval()
        max_ticks = self.axis.get_tick_space()

        if max_ticks > MAX_DATE_TICKS:
            max_ticks = MAX_DATE_TICKS

        return self._tick_values(vmin, vmax, max_ticks=max_ticks)

    def tick_values(self, vmin: float, vmax: float):
        return self._tick_values(vmin, vmax, max_ticks=MAX_DATE_TICKS)

    def _compute_ticks(self, vmin, vmax, max_ticks=10):
        logger.debug("tick_values %r, %r, %r", vmin, vmax, max_ticks)

        if math.isinf(vmin) or math.isinf(vmax):
            return []

        size = len(self.dtarray)
        vmin, vmax = np.round([vmin, vmax]).astype(int).clip(0, size - 1)
        dates = self.dtarray[vmin:vmax+1]

        return vmin + date_ticks(dates, max_ticks)


class DTArrayFormatter(mticker.Formatter):
    """Formatter for a numpy array of datetimes"""

    def __init__(self, dtarray, *, fmt="%Y-%m-%d"):
        self.dtarray = as_dtarray(dtarray)
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


def config_date_axis(ax, dates):
    """Install the date locator and formatter on the axes x-axis.

    Accepts native dates (DatetimeIndex, polars Series, numpy array);
    coerced once and shared by locator and formatter.
    """
    dtarray = as_dtarray(dates)
    ax.xaxis.set_major_locator(DTArrayLocator(dtarray))
    ax.xaxis.set_major_formatter(DTArrayFormatter(dtarray))
