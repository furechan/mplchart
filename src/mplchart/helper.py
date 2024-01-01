"""
helper routines to fetch sample prices in proper OHLCV format
data is fetched via yfinance with some optional caching logic added
please use only for ad hoc testing (see yfinance)
"""

import re
import time
import pathlib
import tempfile
import warnings

import pandas as pd
import yfinance as yf

DEFAULT_MAX_AGE = 24 * 60 * 60
CACHE_FILE_NAME = "mplchart.helper.{params}.csv"

tempdir = pathlib.Path(tempfile.gettempdir())

warnings.warn(
    "The helper module is deprecated. Use your own data source.",
    DeprecationWarning,
    stacklevel=2,
)


def list_cache():
    """lists files in temporary cache"""

    pattern = CACHE_FILE_NAME.format(params="*")
    return list(tempdir.glob(pattern))


def clear_cache(verbose=False):
    """deletes all files in temporary cache"""

    pattern = CACHE_FILE_NAME.format(params="*")
    for file in tempdir.glob(pattern):
        if verbose:
            print(f"Deleting {file.name} ...")
        file.unlink()


def map_frequency(freq):
    """maps loosely defined frequency string to an interval"""

    match = re.fullmatch(r"(\d+)(\w+)", freq)

    if match:
        count = int(match.group(1))
        freq = match.group(2)
    else:
        count = 1

    if freq in ("m", "min", "minute"):
        freq = "m"
    elif freq in ("h", "hour", "hourly"):
        freq = "h"
    elif freq in ("d", "day", "daily"):
        freq = "d"
    elif freq in ("wk", "week", "weekly"):
        freq = "wk"
    elif freq in ("mo", "month", "monthly"):
        freq = "mo"
    else:
        raise ValueError(f"Invalid frequency {freq}!")

    return f"{count}{freq}"


def maximum_period(freq):
    """maps loosely defined frequency string to a maximum period"""

    match = re.fullmatch(r"(\d+)(\w+)", freq)

    if match:
        count = int(match.group(1))
        freq = match.group(2)
    else:
        count = 1

    if freq in ("m", "min", "minute"):
        return "60d" if count > 1 else "7d"

    if freq in ("h", "hour", "hourly"):
        return "60d"

    return "max"


def get_prices(
    ticker: str,
    freq="daily",
    *,
    caching: bool = True,
    verbose: bool = False,
    max_age: float = DEFAULT_MAX_AGE,
):
    """
    function to retrieve sample prices in OHLCV format
    data is fetched via yfinance with some optional caching logic added
    please use only for ad hoc testing (see yfinance)
    """

    cache_file = None
    ticker = ticker.upper()
    interval = map_frequency(freq)
    period = maximum_period(freq)

    if re.fullmatch(r"\d+[mh]", interval):
        # do not cache minute/hourly data
        caching = False

    if caching:
        params = ".".join([ticker, interval, period])
        cache_file = tempdir / CACHE_FILE_NAME.format(params=params)
        if cache_file.exists() and cache_file.stat().st_mtime - time.time() < max_age:
            if verbose:
                print(f"Loading {ticker} data from {cache_file} ...")
            return pd.read_csv(cache_file, index_col=0, parse_dates=True)

    # prices = yf.Ticker(ticker).history(interval=interval, period=period)
    prices = yf.download(
        ticker, interval=interval, period=period, progress=False, auto_adjust=True
    )
    prices = prices.rename(columns=str.lower).rename_axis(index="date")
    prices = prices.filter(["open", "high", "low", "close", "volume"])

    if caching and cache_file:
        if verbose:
            print(f"Saving {ticker} data to {cache_file} ...")
        prices.to_csv(cache_file, lineterminator="\n")

    return prices
