import pytest

from mplchart import samples


@pytest.fixture
def prices():
    return samples.sample_prices()
