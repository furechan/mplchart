""" Sample prices data """

import pandas as pd

from importlib import resources


def sample_prices():
    """Sample prices"""

    res = resources.files(__name__).joinpath("sample-prices.csv")
    with resources.as_file(res) as file:
        return pd.read_csv(file, index_col=0, parse_dates=True)
