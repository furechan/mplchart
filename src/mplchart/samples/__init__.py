""" Sample prices data """

import pandas as pd

from importlib import resources


def sample_prices(max_bars=0):
    """Sample prices"""

    # NOTE that path here is a traversable not a Path object
    path = resources.files(__name__).joinpath("sample-prices.csv")
    with path.open("r") as file:
        prices = pd.read_csv(file, index_col=0, parse_dates=True)
    if max_bars > 0:
        prices = prices.tail(max_bars)
    return prices
