import pytest

import pandas as pd

from mplchart import helper


@pytest.fixture(params=["1min", "5min", "1hour", "daily", "weekly", "monthly"])
def freq(request):
    return request.param


def test_cache():
    helper.get_prices('MSFT')
    res = helper.list_cache()
    assert isinstance(res, list) and len(res) > 0

    helper.clear_cache()
    res = helper.list_cache()
    assert isinstance(res, list) and len(res) == 0


def test_prices(freq):
    data = helper.get_prices('AAPL', freq=freq, caching=False)
    assert isinstance(data, pd.DataFrame) and len(data) >= 100
