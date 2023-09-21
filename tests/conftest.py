import pytest
import pandas as pd

from pathlib import Path


# Arrange
@pytest.fixture
def sample_prices():
    tests = Path(__file__).parent
    file = tests.joinpath("data/sample.csv")
    return pd.read_csv(file, index_col=0)
