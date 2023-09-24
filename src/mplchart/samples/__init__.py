""" Sample prices data """

import pandas as pd

from pathlib import Path


def sample_prices():
    """Sample prices"""

    folder = Path(__file__).parent
    file = folder.joinpath("sample-prices.csv")
    return pd.read_csv(file, index_col=0, parse_dates=True)

