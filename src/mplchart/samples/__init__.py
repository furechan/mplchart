""" Sample prices data """

import pandas as pd

from importlib.resources import open_text


def sample_prices():
    """Sample prices"""

    file = open_text(__name__, "sample-prices.csv")
    return pd.read_csv(file, index_col=0, parse_dates=True)
