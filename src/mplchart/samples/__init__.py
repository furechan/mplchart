""" Sample prices data """

import pandas as pd

from pathlib import Path

from importlib.resources import open_text, is_resource


def sample_prices_old():
    """Sample prices"""

    folder = Path(__file__).parent
    file = folder.joinpath("sample-prices.csv")
    return pd.read_csv(file, index_col=0, parse_dates=True)


def sample_prices():
    """Sample prices"""

    file = open_text(__name__, "sample-prices.csv")
    return pd.read_csv(file, index_col=0, parse_dates=True)

