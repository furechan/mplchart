"""Sample prices data"""

from functools import lru_cache
from importlib import resources


TIMEZONE = "America/New_York"
SAMPLE_FREQUENCIES = "daily", "hourly", "minute"


@lru_cache
def sample_prices(freq: str = "daily", *, max_bars: int = 0, backend: str = "pandas"):
    """Load bundled sample OHLCV prices for testing and examples.

    Results are cached after the first call (per unique combination of arguments).

    Args:
        freq (str): Data frequency. One of ``"daily"``, ``"hourly"``, or
            ``"minute"``. Defaults to ``"daily"``.
        max_bars (int): If greater than 0, return only the most recent
            ``max_bars`` rows. Defaults to 0 (return all rows).
        backend (str): Target DataFrame backend — ``"pandas"`` or ``"polars"``.
            Defaults to ``"pandas"``. The backend module is imported lazily so
            the unused one is not required at runtime.

    Returns:
        DataFrame: OHLCV prices with a datetime index (pandas) or datetime
        column (polars).
    """

    fname = f"{freq}-prices.csv"
    path = resources.files(__name__).joinpath(fname)
    # Note that path here is a traversable not a Path object

    match backend:
        case "pandas":
            return _load_pandas(path, freq=freq, max_bars=max_bars)
        case "polars":
            return _load_polars(path, freq=freq, max_bars=max_bars)
        case _:
            raise ValueError(f"Unknown backend {backend!r}")


def _load_pandas(path, *, freq: str, max_bars: int):
    import pandas as pd

    with path.open("r") as file:
        prices = pd.read_csv(file, index_col=0, parse_dates=True)

    if freq != "daily":
        prices.index = pd.to_datetime(prices.index, utc=True).tz_convert(TIMEZONE)

    if max_bars > 0:
        prices = prices.tail(max_bars)

    return prices


def _load_polars(path, *, freq: str, max_bars: int):
    import polars as pl

    with path.open("rb") as file:
        prices = pl.read_csv(file, try_parse_dates=True)

    col = prices.columns[0]  # temporal column — "date" (daily) or "datetime" (hourly/minute)

    if freq != "daily":
        tz = getattr(prices.schema[col], "time_zone", None)
        if tz is None:
            prices = prices.with_columns(
                pl.col(col).dt.replace_time_zone("UTC").dt.convert_time_zone(TIMEZONE)
            )
        else:
            prices = prices.with_columns(pl.col(col).dt.convert_time_zone(TIMEZONE))

    if max_bars > 0:
        prices = prices.tail(max_bars)

    return prices
