""" Sample prices data """

import pandas as pd

from functools import lru_cache
from importlib import resources

from ..utils import convert_dataframe


TIMEZONE = "America/New_York"
SAMPLE_FREQUENCIES = "daily", "hourly", "minute"


@lru_cache
def sample_prices(freq: str = "daily", *, max_bars: int = 0, backend: str | None = None):
    """Load bundled sample OHLCV prices for testing and examples.

    Results are cached after the first call (per unique combination of arguments).

    Args:
        freq (str): Data frequency. One of ``"daily"``, ``"hourly"``, or
            ``"minute"``. Defaults to ``"daily"``.
        max_bars (int): If greater than 0, return only the most recent
            ``max_bars`` rows. Defaults to 0 (return all rows).
        backend (str, optional): Target DataFrame backend. Pass ``"polars"``
            to convert the result to a Polars DataFrame. Defaults to ``None``
            (returns a pandas DataFrame).

    Returns:
        DataFrame: OHLCV prices with a datetime index (pandas) or datetime
        column (Polars).
    """

    fname = f"{freq}-prices.csv"
    path = resources.files(__name__).joinpath(fname)
    # Note that path here is a traversable not a Path object

    with path.open("r") as file:
        prices = pd.read_csv(file, index_col=0, parse_dates=True)

    if freq != "daily":
        prices.index = pd.to_datetime(prices.index, utc=True).tz_convert(TIMEZONE)

    if max_bars > 0:
        prices = prices.tail(max_bars)

    if backend is not None:
        prices = convert_dataframe(prices, backend)

    return prices
