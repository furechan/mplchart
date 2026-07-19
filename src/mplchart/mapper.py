"""Date mappers — backend-native windowing and x-coordinate machinery.

The contract is the ``DateMapper`` ABC; ``get_mapper`` routes on the prices
backend. ``raw_dates`` is a mode flag: it changes what ``xloc`` holds
(integer rownums vs the datetimes themselves) and what ``map_date`` /
``config_axes`` do — never which class runs.
"""

import numpy as np

from abc import ABC, abstractmethod
from datetime import datetime

from .locators import DTArrayLocator
from .formatters import DTArrayFormatter


class DateMapper(ABC):
    """Pure contract for date mappers — no state at this level.

    Subclasses are backend-specific: they take the prices frame, derive and
    store dates and x-coordinates natively, and implement all data operations
    in their own backend. numpy appears only at the matplotlib boundary.
    """

    raw_dates: bool = False

    @abstractmethod
    def slice(self, data, *, xcol=None):
        """Slice prices-aligned data to the visible window.

        If ``xcol`` is given, the result carries an extra column of that name
        with per-row x-coordinates.
        """
        ...

    @abstractmethod
    def series_xy(self, *series):
        """Return (x, *windowed_series) numpy arrays.

        Positional contract: each series must be full-length in prices row
        order; all series are cut by the same window against one shared x.
        """
        ...

    @abstractmethod
    def map_date(self, date):
        """Map a single date to its x-coordinate."""
        ...

    @abstractmethod
    def _dt_array(self) -> np.ndarray:
        """Full datetime array as numpy — for the axis locator/formatter."""
        ...

    def config_axes(self, ax):
        """Configure the x-axis; rownum mode installs the date locator/formatter."""
        if self.raw_dates:
            return
        arr = self._dt_array()
        ax.xaxis.set_major_locator(DTArrayLocator(arr))
        ax.xaxis.set_major_formatter(DTArrayFormatter(arr))


class PandasDateMapper(DateMapper):
    """Pandas-native date mapper.

    Stores dates as a tz-naive DatetimeIndex and ``xloc`` as a date-indexed
    Series (integer rownums, or the dates themselves in ``raw_dates`` mode).
    Slicing joins prices-aligned data on that series.
    """

    def __init__(self, prices, *, raw_dates=False, start=None, end=None, max_bars=None):
        import pandas as pd

        self.raw_dates = raw_dates
        self.start = start
        self.end = end
        self.max_bars = max_bars

        dates = prices.index
        if dates.tz is not None:
            dates = dates.tz_localize(None)
        self.dates = pd.DatetimeIndex(dates)

        values = self.dates if raw_dates else np.arange(len(self.dates))
        self.xloc = pd.Series(values, index=self.dates, name="xloc")

    @staticmethod
    def _to_datetime(value):
        """Coerce a date-like value to a tz-naive Timestamp (a datetime subclass)."""
        import pandas as pd

        ts = pd.Timestamp(value)
        if ts.tzinfo is not None:
            ts = ts.tz_localize(None)
        return ts

    def _window(self) -> slice:
        """Visible window as an absolute row slice; end is inclusive."""
        lo, hi = 0, len(self.dates)
        if self.start is not None:
            lo = int(self.dates.searchsorted(self._to_datetime(self.start)))
        if self.end is not None:
            hi = int(self.dates.searchsorted(self._to_datetime(self.end), side="right"))
        if self.max_bars and self.max_bars > 0:
            lo = max(lo, hi - self.max_bars)
        return slice(lo, hi)

    def slice(self, data, *, xcol=None):
        w = self._window()
        xloc = self.xloc.iloc[w]

        if hasattr(data.index, "tz") and data.index.tz is not None:
            data = data.set_axis(data.index.tz_localize(None))

        xloc, data = xloc.align(data, join="inner")
        data = data.set_axis(xloc)
        if xcol is not None:
            data = data.copy()
            data[xcol] = data.index.values
        return data

    def series_xy(self, *series):
        w = self._window()
        xs = self.xloc.to_numpy()[w]
        return (xs, *(np.asarray(self._check_length(s))[w] for s in series))

    def _check_length(self, value):
        if len(value) != len(self.dates):
            raise ValueError(
                f"series_xy expects full-length values aligned with prices "
                f"({len(self.dates)} rows), got {len(value)}"
            )
        return value

    def map_date(self, date):
        ts = self._to_datetime(date)
        if self.raw_dates:
            return ts.to_datetime64()
        return int(self.dates.searchsorted(ts))

    def _dt_array(self) -> np.ndarray:
        return self.dates.to_numpy()


class PolarsDateMapper(DateMapper):
    """Polars-native date mapper.

    Stores dates as a tz-naive Datetime Series and ``xloc`` as a Series
    (integer rownums, or the dates themselves in ``raw_dates`` mode).
    Slicing is positional — data is assumed full-length in prices row order.
    """

    def __init__(self, prices, *, raw_dates=False, start=None, end=None, max_bars=None):
        import polars as pl

        self.raw_dates = raw_dates
        self.start = start
        self.end = end
        self.max_bars = max_bars

        col = next(
            (prices[name] for name, dtype in prices.schema.items()
             if dtype == pl.Date or dtype == pl.Datetime),
            None,
        )
        if col is None:
            raise ValueError("No Date or Datetime column found in DataFrame")
        if col.dtype == pl.Date:
            self.dates = col.cast(pl.Datetime("us"))
        else:
            self.dates = col.dt.replace_time_zone(None)

        if raw_dates:
            self.xloc = self.dates.alias("xloc")
        else:
            self.xloc = pl.int_range(len(self.dates), eager=True).alias("xloc")

    @staticmethod
    def _to_datetime(value) -> datetime:
        """Coerce a date-like value to a tz-naive python datetime."""
        if hasattr(value, "tzinfo") and value.tzinfo is not None:
            value = value.replace(tzinfo=None)
        return np.datetime64(value, "us").item()  # type: ignore  # numpy stubs type .item() as a union

    def _window(self) -> slice:
        """Visible window as an absolute row slice; end is inclusive."""
        lo, hi = 0, len(self.dates)
        if self.start is not None:
            lo = int(self.dates.search_sorted(self._to_datetime(self.start)))
        if self.end is not None:
            hi = int(self.dates.search_sorted(self._to_datetime(self.end), side="right"))
        if self.max_bars and self.max_bars > 0:
            lo = max(lo, hi - self.max_bars)
        return slice(lo, hi)

    def slice(self, data, *, xcol=None):
        w = self._window()
        sliced = data[w]
        if xcol is not None:
            sliced = sliced.with_columns(self.xloc[w].alias(xcol))
        return sliced

    def series_xy(self, *series):
        import polars as pl

        w = self._window()
        xs = self.xloc[w].to_numpy()
        return (xs, *(
            s[w].to_numpy() if isinstance(self._check_length(s), pl.Series)
            else np.asarray(s)[w]
            for s in series
        ))

    def _check_length(self, value):
        if len(value) != len(self.dates):
            raise ValueError(
                f"series_xy expects full-length values aligned with prices "
                f"({len(self.dates)} rows), got {len(value)}"
            )
        return value

    def map_date(self, date):
        dt = self._to_datetime(date)
        if self.raw_dates:
            return np.datetime64(dt)
        return int(self.dates.search_sorted(dt))

    def _dt_array(self) -> np.ndarray:
        return self.dates.to_numpy()


def get_mapper(prices, *, raw_dates=False, start=None, end=None, max_bars=None) -> DateMapper:
    """Create the backend-native date mapper for a prices frame."""
    from .utils import detect_backend

    match detect_backend(prices):
        case "polars":
            cls = PolarsDateMapper
        case "pandas":
            cls = PandasDateMapper
        case backend:
            raise ValueError(f"Unsupported backend {backend!r}")

    return cls(prices, raw_dates=raw_dates, start=start, end=end, max_bars=max_bars)
