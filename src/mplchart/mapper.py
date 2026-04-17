"""date mapper"""

import numpy as np

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

    def map_date(self, date):
        return date

    def config_axes(self, ax):
        pass


class DateIndexMapper:
    """Date Index Mapper — maps dates to integer row positions (rownum).

    Stores the full tz-naive numpy datetime array and computes the visible
    window as an absolute slice via calc_window(). Indicators are computed
    on the full dataset; only the final slice is handed to the plotter.

    Args:
        datetime_array: Full datetime array from the prices DataFrame.
        max_bars: Maximum number of bars to show (from the end).
        start: Start datetime filter.
        end: End datetime filter.
    """

    def __init__(self, datetime_array: np.ndarray, *, max_bars=None, start=None, end=None):
        self.datetime_array = np.asarray(datetime_array, dtype="datetime64[ns]")
        self.rownum = np.arange(len(self.datetime_array))
        self.max_bars = max_bars
        self.start = start
        self.end = end

    def calc_window(self) -> slice:
        """Return the visible window as an absolute slice into datetime_array."""
        dt = self.datetime_array
        lo, hi = 0, len(dt)

        if self.start is not None:
            lo = int(np.searchsorted(dt, np.datetime64(self.start, "ns")))
        if self.end is not None:
            hi = int(np.searchsorted(dt, np.datetime64(self.end, "ns"), side="right"))
        if self.max_bars and self.max_bars > 0:
            lo = max(lo, hi - self.max_bars)

        return slice(lo, hi)

    def series_xy(self, values, window: slice):
        """Return (x, y) numpy arrays for a full-length values array.

        ``values`` must be the same length as the full datetime_array.
        ``window`` is an absolute slice as returned by calc_window().
        """
        return self.rownum[window], np.asarray(values)[window]

    def slice(self, data):
        """Slice data to the visible window, dispatching by backend."""
        if hasattr(data, "index"):
            return self.slice_pandas(data)
        return self.slice_polars(data)

    def slice_polars(self, data):
        """Positional slice — assumes full-length, rownum-positional data."""
        window = self.calc_window()
        return data[window]

    def slice_pandas(self, data):
        """Align pandas data by datetime and re-index to rownum positions."""
        import pandas as pd

        window = self.calc_window()
        dt = self.datetime_array[window]
        xloc = pd.Series(self.rownum[window], index=pd.DatetimeIndex(dt), name="xloc")

        if hasattr(data.index, "tz") and data.index.tz is not None:
            data = data.set_axis(data.index.tz_localize(None))

        xloc, data = xloc.align(data, join="inner")
        data = data.set_axis(xloc)
        return data

    def map_date(self, date) -> int:
        """Map a single date to its rownum (for plot_vline)."""
        return int(np.searchsorted(self.datetime_array, np.datetime64(date, "ns"), side="left"))

    def config_axes(self, ax):
        """Set locator and formatter on the x-axis using the full datetime array."""
        locator = DTArrayLocator(self.datetime_array)
        formatter = DTArrayFormatter(self.datetime_array)

        if locator:
            ax.xaxis.set_major_locator(locator)
        if formatter:
            ax.xaxis.set_major_formatter(formatter)
