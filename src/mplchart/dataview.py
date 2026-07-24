"""Data views — backend-native windowing and x-coordinate machinery.

The contract is the ``DataView`` ABC; ``get_view`` routes on the prices
backend. ``raw_dates`` is a mode flag: it changes what ``xloc`` holds
(integer rownums vs the datetimes themselves) and what ``map_date`` does —
never which class runs. Evaluation is native per view: each subclass
implements ``eval`` in full for its own item forms (column string, native
expressions, callable) — no backend branch, no shared dispatch. Axis wiring
lives outside the view: the composition layer reads ``dates`` and installs
the dateaxis machinery when not ``raw_dates``. This module is matplotlib-free.
"""

import numpy as np

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from .utils import detect_backend, is_polars_expr, is_pandas_expr, is_series_data


class DataView(ABC):
    """Pure contract for data views — no state at this level.

    Subclasses are backend-specific: they take the prices frame, derive and
    store dates and x-coordinates natively, and implement all data operations
    in their own backend. numpy appears only at the matplotlib boundary.

    ``prices`` is part of the contract: the wrapped full-length prices frame
    in its native backend, as supplied at construction. The view is a ranged
    view over it — ``eval`` computes against the full frame, ``slice`` and
    ``series_xy`` window prices-aligned data. It is the supported way to
    reach the frame (``chart.view.prices``); the frame is not stored
    anywhere else.

    ``dates`` is part of the contract: the full datetime array in native form
    (DatetimeIndex / polars Series). Its consumer is the dateaxis machinery,
    which accepts any datetime array-like and coerces to numpy at its own
    boundary — dateaxis may eventually consume the view directly; for now
    the surface between them is ``dates``.
    """

    raw_dates: bool = False
    prices: Any  # contract attribute — see class docstring
    dates: Any  # contract attribute — see class docstring

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
    def eval(self, item):
        """Evaluate an indicator or expression — or adopt already-computed data.

        Returns a full-length native result — no windowing. Each backend
        implements its own dispatch: column string, its native expression
        type, callable, and series data (array-likes are adopted and
        aligned — the view is the only layer that can align by date; see
        each backend's data branch). Native expressions must be checked
        before the callable fallback (pandas Expressions are callable). An
        item the receiving view doesn't recognize raises ``TypeError``.
        """
        ...


class PandasDataView(DataView):
    """Pandas-native data view.

    Stores dates as a tz-naive DatetimeIndex and ``xloc`` as a date-indexed
    Series (integer rownums, or the dates themselves in ``raw_dates`` mode).
    Slicing joins prices-aligned data on that series.
    """

    def __init__(self, prices, *, raw_dates=False, start=None, end=None, max_bars=None):
        import pandas as pd

        self.prices = prices
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

    def eval(self, item):
        if isinstance(item, str):
            return self.prices[item]

        if is_pandas_expr(item):
            return item._eval_expression(self.prices)

        if is_series_data(item):
            return self._adopt_data(item)

        if callable(item):
            return item(self.prices)

        raise TypeError(
            f"PandasDataView cannot evaluate {type(item).__name__!r}: "
            f"expected a column name, pandas Expression, callable indicator, "
            f"or series data."
        )

    def _adopt_data(self, data):
        """Adopt already-computed data.

        Date-indexed input aligns to the prices index (tz-stripped,
        reindexed — partial or reordered data is fine); anything else is
        positional and must be full-length in prices row order.
        """
        index = getattr(data, "index", None)
        if index is not None and hasattr(index, "tz"):
            if index.tz is not None:
                data = data.set_axis(index.tz_localize(None))
            return data.reindex(self.dates)

        if len(data) != len(self.dates):
            raise ValueError(
                f"data must be full-length aligned with prices "
                f"({len(self.dates)} rows), got {len(data)}"
            )
        return data


class PolarsDataView(DataView):
    """Polars-native data view.

    Stores dates as a tz-naive Datetime Series and ``xloc`` as a Series
    (integer rownums, or the dates themselves in ``raw_dates`` mode).
    Slicing is positional — data is assumed full-length in prices row order.
    """

    def __init__(self, prices, *, raw_dates=False, start=None, end=None, max_bars=None):
        import polars as pl

        self.prices = prices
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

    def eval(self, item):
        import polars as pl

        if isinstance(item, str):
            return self.prices[item]

        if is_polars_expr(item):
            series = self.prices.select(item).to_series()
            if isinstance(series.dtype, pl.Struct):
                return series.struct.unnest()
            return series

        if isinstance(item, tuple) and item and all(is_polars_expr(e) for e in item):
            series = [self.prices.select(e).to_series() for e in item]
            return pl.DataFrame({s.name: s for s in series})

        if is_series_data(item):
            # polars data carries no index — positional, full-length only
            if len(item) != len(self.dates):
                raise ValueError(
                    f"data must be full-length in prices row order "
                    f"({len(self.dates)} rows), got {len(item)}"
                )
            return item

        if callable(item):
            return item(self.prices)

        raise TypeError(
            f"PolarsDataView cannot evaluate {type(item).__name__!r}: "
            f"expected a column name, polars Expr, tuple of Expr, callable "
            f"indicator, or series data."
        )


def get_view(prices, *, raw_dates=False, start=None, end=None, max_bars=None) -> DataView:
    """Create the backend-native data view for a prices frame."""
    match detect_backend(prices):
        case "polars":
            cls = PolarsDataView
        case "pandas":
            cls = PandasDataView
        case backend:
            raise ValueError(f"Unsupported backend {backend!r}")

    return cls(prices, raw_dates=raw_dates, start=start, end=end, max_bars=max_bars)
