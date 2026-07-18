"""Indicator tests — pandas backend"""

import pytest
import matplotlib.pyplot as plt

pytest.importorskip("pandas")
pytestmark = pytest.mark.pandas

from mplchart.chart import Chart  # noqa: E402
from mplchart.samples import sample_prices  # noqa: E402
from mplchart.primitives import Candlesticks, Volume  # noqa: E402
from mplchart.indicators import (  # noqa: E402
    SMA, EMA, WMA, HMA,
    RSI, ATR, NATR, ADX,
    MACD, PPO,
    BBANDS, STOCH, CMF, BOP, MFI,
)


FREQS = ["daily", "hourly", "minute"]

INDICATORS = [
    Volume(),
    SMA(20),
    EMA(20),
    WMA(20),
    HMA(20),
    RSI(),
    ATR(),
    NATR(),
    ADX(),
    MACD(),
    PPO(),
    BBANDS(),
    STOCH(),

    CMF(),
    BOP(),
    MFI(),
]


@pytest.mark.parametrize("freq", FREQS)
def test_prices(freq):
    prices = sample_prices(freq=freq)
    assert len(prices) > 0


def test_prices_invalid_freq():
    with pytest.raises(ValueError, match="weekly"):
        sample_prices(freq="weekly")


@pytest.mark.parametrize("freq", FREQS)
@pytest.mark.parametrize("indicator", INDICATORS, ids=str)
def test_indicators(indicator, freq, max_bars=250):
    prices = sample_prices(freq=freq)
    chart = Chart(prices, title="Test", max_bars=max_bars)
    chart.plot([Candlesticks(), indicator])
    assert chart.count_axes() > 0
    plt.close()


def test_stoch_params():
    """STOCH must honor fastn/slown (regression: they were silently ignored)"""
    prices = sample_prices()
    assert not STOCH(14, 3, 3)(prices).equals(STOCH(14, 5, 5)(prices))


def test_indicator_chain_indicator_to_indicator():
    chained = SMA(20) | EMA(5)
    prices = sample_prices()
    result = chained(prices)
    assert len(result) == len(prices)


def test_indicator_or_rejects_lambda():
    with pytest.raises(TypeError):
        SMA(20) | (lambda s: s.rolling(3).mean())


def test_indicator_apply_via_pipe():
    prices = sample_prices()
    result = prices.pipe(SMA(20))
    assert len(result) == len(prices)
