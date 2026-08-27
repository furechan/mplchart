"""Numeric parity tests — pandas indicators vs polars expressions"""

import pytest
import numpy as np

pytest.importorskip("pandas")
pl = pytest.importorskip("polars")
pytestmark = [pytest.mark.pandas, pytest.mark.polars]

from mplchart import indicators as ind  # noqa: E402
from mplchart import expressions as xp  # noqa: E402
from mplchart.samples import sample_prices  # noqa: E402


# DMI/ADX are excluded: a floating-point tie between +DM and -DM on a single
# sample row breaks differently per backend (1-ulp difference in -low.diff())
# and the flipped branch shifts the smoothed values. Formulas are equivalent.
PAIRS = [
    ("SMA(20)", ind.SMA(20), xp.SMA(20)),
    ("EMA(20)", ind.EMA(20), xp.EMA(20)),
    ("WMA(20)", ind.WMA(20), xp.WMA(20)),
    ("HMA(15)", ind.HMA(15), xp.HMA(15)),
    ("HMA(20)", ind.HMA(20), xp.HMA(20)),
    ("RMA(14)", ind.RMA(14), xp.RMA(14)),
    ("DEMA(20)", ind.DEMA(20), xp.DEMA(20)),
    ("TEMA(20)", ind.TEMA(20), xp.TEMA(20)),
    ("ROC()", ind.ROC(), xp.ROC()),
    ("MOM(10)", ind.MOM(10), xp.MOM(10)),
    ("RSI(14)", ind.RSI(14), xp.RSI(14)),
    ("ATR(14)", ind.ATR(14), xp.ATR(14)),
    ("NATR(14)", ind.NATR(14), xp.NATR(14)),
    ("MACD()", ind.MACD(), xp.MACD()),
    ("PPO()", ind.PPO(), xp.PPO()),
    ("STOCH()", ind.STOCH(), xp.STOCH()),
    ("BBANDS()", ind.BBANDS(), xp.BBANDS()),
    ("KELTNER()", ind.KELTNER(), xp.KELTNER()),
    ("DONCHIAN()", ind.DONCHIAN(), xp.DONCHIAN()),
]

# rows to skip before comparing — lets ewm-based indicators converge
SKIP = 100


@pytest.mark.parametrize("indicator,expression", [p[1:] for p in PAIRS], ids=[p[0] for p in PAIRS])
def test_backend_parity(indicator, expression):
    pd_prices = sample_prices(backend="pandas")
    pl_prices = sample_prices(backend="polars")

    pd_result = np.asarray(indicator(pd_prices).to_numpy(), dtype=float)

    series = pl_prices.select(expression).to_series()
    if isinstance(series.dtype, pl.Struct):
        pl_result = series.struct.unnest().to_numpy()
    else:
        pl_result = series.to_numpy()
    pl_result = np.asarray(pl_result, dtype=float)

    assert pd_result.shape == pl_result.shape
    assert np.allclose(pd_result[SKIP:], pl_result[SKIP:], rtol=1e-9, equal_nan=True)


def test_roc_and_natr_are_scaled_to_100():
    pd_prices = sample_prices(backend="pandas")
    pl_prices = sample_prices(backend="polars")

    expected_roc = pd_prices["close"].pct_change() * 100
    pd_roc = ind.ROC()(pd_prices)
    pl_roc = pl_prices.select(xp.ROC()).to_series().to_numpy()
    assert np.allclose(pd_roc, expected_roc, equal_nan=True)
    assert np.allclose(pl_roc, expected_roc, equal_nan=True)

    pd_atr = ind.ATR()(pd_prices)
    expected_natr = pd_atr / pd_prices["close"] * 100
    pd_natr = ind.NATR()(pd_prices)
    pl_natr = pl_prices.select(xp.NATR()).to_series().to_numpy()
    assert np.allclose(pd_natr, expected_natr, equal_nan=True)
    assert np.allclose(pl_natr[SKIP:], expected_natr[SKIP:], rtol=1e-9, equal_nan=True)
