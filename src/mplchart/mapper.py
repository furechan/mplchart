"""date mapper"""

import numpy as np

from .locators import DTArrayLocator
from .formatters import DTArrayFormatter


def _resolve_window(datetime_array, start, end, max_bars) -> slice:
    """Resolve start/end/max_bars into an absolute slice into datetime_array."""
    lo, hi = 0, len(datetime_array)
    if start is not None:
        lo = int(np.searchsorted(datetime_array, np.datetime64(start, "ns")))
    if end is not None:
        hi = int(np.searchsorted(datetime_array, np.datetime64(end, "ns"), side="right"))
    if max_bars and max_bars > 0:
        lo = max(lo, hi - max_bars)
    return slice(lo, hi)


class DateIndexMapper:
    """Date Index Mapper — maps dates to integer row positions (rownum).

    Stores the full tz-naive numpy datetime array; the visible window is
    resolved internally from ``start`` / ``end`` / ``max_bars``. Indicators
    are computed on the full dataset; only the final slice is handed to
    the plotter.
    X-axis coordinates are integer rownums; ``DTArrayLocator`` /
    ``DTArrayFormatter`` map those ticks back to date labels.

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

    def _calc_window(self) -> slice:
        """Return the visible window as an absolute slice into datetime_array."""
        return _resolve_window(self.datetime_array, self.start, self.end, self.max_bars)

    def series_xy(self, *values):
        """Return (x, *sliced_values) numpy arrays.

        Each positional argument must be a full-length array the same
        length as ``datetime_array``; each is sliced to the same window.

            xs, y = mapper.series_xy(y)
            xs, flag, close = mapper.series_xy(flag, close)

        x is ``rownum[window]`` — integer row positions.
        """
        window = self._calc_window()
        xs = self.rownum[window]
        return (xs, *(np.asarray(v)[window] for v in values))

    def slice(self, data, *, xcol=None):
        """Slice data to the visible window, dispatching by backend.

        If ``xcol`` is given, adds a column of that name to the result
        carrying the x-coordinates (rownum values) for the window.
        """
        if hasattr(data, "index"):
            return self.slice_pandas(data, xcol=xcol)
        return self.slice_polars(data, xcol=xcol)

    def slice_polars(self, data, *, xcol=None):
        """Positional slice — assumes full-length, rownum-positional data."""
        import polars as pl

        window = self._calc_window()
        sliced = data[window]
        if xcol is not None:
            sliced = sliced.with_columns(pl.Series(xcol, self.rownum[window]))
        return sliced

    def slice_pandas(self, data, *, xcol=None):
        """Align pandas data by datetime and re-index to rownum positions."""
        import pandas as pd

        window = self._calc_window()
        dt = self.datetime_array[window]
        xloc = pd.Series(self.rownum[window], index=pd.DatetimeIndex(dt), name="xloc")

        if hasattr(data.index, "tz") and data.index.tz is not None:
            data = data.set_axis(data.index.tz_localize(None))

        xloc, data = xloc.align(data, join="inner")
        data = data.set_axis(xloc)
        if xcol is not None:
            data = data.copy()
            data[xcol] = data.index.values
        return data

    def map_date(self, date) -> int:
        """Map a single date to its x-coordinate (rownum position)."""
        return int(np.searchsorted(self.datetime_array, np.datetime64(date, "ns"), side="left"))

    def config_axes(self, ax):
        """Set locator and formatter on the x-axis using the full datetime array."""
        locator = DTArrayLocator(self.datetime_array)
        formatter = DTArrayFormatter(self.datetime_array)

        if locator:
            ax.xaxis.set_major_locator(locator)
        if formatter:
            ax.xaxis.set_major_formatter(formatter)


class RawDateMapper:
    """Raw Date Mapper — uses datetime values as x-axis coordinates.

    Alternative to ``DateIndexMapper`` that skips the integer rownum
    indirection. X-axis coordinates are actual ``datetime64`` values, and
    matplotlib's built-in date handling takes care of tick placement and
    formatting — no custom locator/formatter required.

    Offers the same public interface as ``DateIndexMapper`` so chart and
    primitive code is agnostic to the mapper choice. The only semantic
    difference is that ``rownum`` / ``series_xy``'s x values are datetimes
    rather than integer positions.

    Args:
        datetime_array: Full datetime array from the prices DataFrame.
        max_bars: Maximum number of bars to show (from the end).
        start: Start datetime filter.
        end: End datetime filter.
    """

    def __init__(self, datetime_array: np.ndarray, *, max_bars=None, start=None, end=None):
        self.datetime_array = np.asarray(datetime_array, dtype="datetime64[ns]")
        # `rownum` on RawDateMapper returns the datetime array itself, so
        # primitives using `chart.mapper.rownum[window]` get date-valued xs.
        self.rownum = self.datetime_array
        self.max_bars = max_bars
        self.start = start
        self.end = end

    def _calc_window(self) -> slice:
        """Return the visible window as an absolute slice into datetime_array."""
        return _resolve_window(self.datetime_array, self.start, self.end, self.max_bars)

    def series_xy(self, *values):
        """Return (x, *sliced_values) numpy arrays.

        Each positional argument must be a full-length array the same
        length as ``datetime_array``; each is sliced to the same window.
        x is ``datetime_array[window]`` — actual datetime values.
        """
        window = self._calc_window()
        xs = self.datetime_array[window]
        return (xs, *(np.asarray(v)[window] for v in values))

    def slice(self, data, *, xcol=None):
        """Slice data to the visible window, dispatching by backend.

        If ``xcol`` is given, adds a column of that name carrying the
        x-coordinates (datetime values) for the window.
        """
        if hasattr(data, "index"):
            return self.slice_pandas(data, xcol=xcol)
        return self.slice_polars(data, xcol=xcol)

    def slice_polars(self, data, *, xcol=None):
        """Positional slice — assumes full-length polars data."""
        import polars as pl

        window = self._calc_window()
        sliced = data[window]
        if xcol is not None:
            sliced = sliced.with_columns(pl.Series(xcol, self.datetime_array[window]))
        return sliced

    def slice_pandas(self, data, *, xcol=None):
        """Slice pandas data by date range; preserves the datetime index."""
        window = self._calc_window()
        if window.stop <= window.start:
            return data.iloc[0:0]
        start = self.datetime_array[window.start]
        end = self.datetime_array[window.stop - 1]
        if hasattr(data.index, "tz") and data.index.tz is not None:
            data = data.set_axis(data.index.tz_localize(None))
        sliced = data.loc[start:end]
        if xcol is not None:
            sliced = sliced.copy()
            sliced[xcol] = sliced.index.values
        return sliced

    def map_date(self, date):
        """Map a single date to its x-coordinate (the date itself)."""
        return np.datetime64(date, "ns")

    def config_axes(self, ax):
        """No-op — matplotlib handles datetime axes natively."""
        pass
