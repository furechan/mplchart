""" Sample prices data """

import pandas as pd

from importlib import resources


def sample_prices():
    """Sample prices"""

    # path is a trversable not a Path object
    path = resources.files(__name__).joinpath("sample-prices.csv")
    with path.open("r") as file:
        return pd.read_csv(file, index_col=0, parse_dates=True)
