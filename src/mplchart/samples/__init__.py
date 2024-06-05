""" Sample prices data """

import pandas as pd

from importlib import resources

TIMEZONE = "America/New_York"


def sample_prices(freq: str = "daily", *, max_bars: int = 0):
    """Sample prices"""

    fname = f"{freq}-prices.csv"
    path = resources.files(__name__).joinpath(fname)
    # Note that path here is a traversable not a Path object

    with path.open("r") as file:
        prices = pd.read_csv(file, index_col=0, parse_dates=True)

    if freq != "daily":
        prices.index = pd.to_datetime(prices.index, utc=True).tz_convert(TIMEZONE)

    if max_bars > 0:
        prices = prices.tail(max_bars)

    return prices
