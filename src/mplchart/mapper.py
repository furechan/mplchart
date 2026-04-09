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

    Stores a tz-naive numpy datetime array and computes a window slice
    via np.searchsorted. No pandas dependency.
    """

    def __init__(self, datetime_array: np.ndarray, *, max_bars=None, start=None, end=None):
        datetime_array = np.asarray(datetime_array, dtype="datetime64[ns]")

        lo, hi = 0, len(datetime_array)

        if start is not None:
            lo = int(np.searchsorted(datetime_array, np.datetime64(start, "ns")))
        if end is not None:
            hi = int(np.searchsorted(datetime_array, np.datetime64(end, "ns"), side="right"))

        datetime_array = datetime_array[lo:hi]

        if max_bars and max_bars > 0:
            datetime_array = datetime_array[-max_bars:]

        self.datetime_array = datetime_array
        self.rownum = np.arange(len(datetime_array))

    def calc_window(self, start=None, end=None, max_bars=None) -> slice:
        """Return a slice(start_row, end_row) for the visible bar range."""
        lo, hi = 0, len(self.datetime_array)

        if start is not None:
            lo = int(np.searchsorted(self.datetime_array, np.datetime64(start, "ns")))
        if end is not None:
            hi = int(np.searchsorted(self.datetime_array, np.datetime64(end, "ns"), side="right"))
        if max_bars and max_bars > 0:
            lo = max(lo, hi - max_bars)

        return slice(lo, hi)

    def series_xy(self, values, window: slice):
        """Return (x, y) numpy arrays for the given window."""
        return self.rownum[window], np.asarray(values)[window]

    def slice(self, data):
        """Legacy slice — maps data index to rownum positions.

        Used by existing indicator/primitive code until primitives are
        fully migrated to series_xy. Returns data re-indexed to integer
        row positions (pandas) or positionally sliced (polars).
        """
        import pandas as pd

        window = self.calc_window()

        # polars: positional slice (same-length result, no index)
        if not hasattr(data, "index"):
            return data[window]

        dt = self.datetime_array[window]
        xloc = pd.Series(self.rownum[window], index=pd.DatetimeIndex(dt), name="xloc")

        # strip tz from data index if needed to allow alignment with tz-naive xloc
        if hasattr(data.index, "tz") and data.index.tz is not None:
            data = data.set_axis(data.index.tz_localize(None))

        xloc, data = xloc.align(data, join="inner")
        data = data.set_axis(xloc)
        return data

    def map_date(self, date) -> int:
        """Map a single date to its rownum (for plot_vline)."""
        return int(np.searchsorted(self.datetime_array, np.datetime64(date, "ns"), side="left"))

    def config_axes(self, ax):
        """Set locator and formatter on the x-axis."""
        locator = DTArrayLocator(self.datetime_array)
        formatter = DTArrayFormatter(self.datetime_array)

        if locator:
            ax.xaxis.set_major_locator(locator)
        if formatter:
            ax.xaxis.set_major_formatter(formatter)
