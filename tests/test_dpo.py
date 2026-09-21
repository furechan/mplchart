"""DPO formula and alignment tests for both backends."""

import numpy as np
import pytest


@pytest.fixture(params=["pandas", "polars"])
def evaluate(request):
    backend = pytest.importorskip(request.param)
    if request.param == "pandas":
        from mplchart.indicators import DPO

        def evaluate(values, period=20, source="close"):
            series = backend.Series(values, dtype=float, index=backend.date_range("2020-01-01", periods=len(values)))
            result = DPO(period)(series if source != "close" else series.to_frame("close"))
            assert result.index.equals(series.index)
            return result.to_numpy()
    else:
        from mplchart.expressions import DPO

        def evaluate(values, period=20, source="close"):
            frame = backend.DataFrame({source: backend.Series(values, dtype=backend.Float64)})
            expr = DPO(period) if source == "close" else DPO(period, src=backend.col(source))
            result = frame.lazy().select(expr).collect().to_series()
            assert result.name == "dpo"
            return result.to_numpy()
    return evaluate


@pytest.mark.parametrize("source", ["close", "open"])
@pytest.mark.parametrize("period,expected", [
    (4, [-3.75, -2.5, -1.75, -3.5, np.nan, np.nan, np.nan]),
    (5, [np.nan, -1.4, -0.6, -3.2, np.nan, np.nan, np.nan]),
])
def test_dpo_known_values(evaluate, period, expected, source):
    # Hand-calculated windows for irregular prices catch shift direction and rounding.
    values = [2., 5., 9., 7., 9., 18., 8.]
    np.testing.assert_allclose(evaluate(values, period, source), expected, equal_nan=True)


def test_dpo_default_period(evaluate):
    result = evaluate(list(range(30)))
    assert np.isnan(result[:8]).all()
    np.testing.assert_allclose(result[8:-11], -1.5)
    assert np.isnan(result[-11:]).all()


@pytest.mark.parametrize("values", [[], [1., 2., 3.]])
def test_dpo_insufficient_history(evaluate, values):
    result = evaluate(values)
    assert len(result) == len(values)
    assert np.isnan(result).all()


def test_dpo_constant_prices(evaluate):
    np.testing.assert_allclose(evaluate([7.] * 30)[8:-11], 0.)


def test_dpo_period_one(evaluate):
    np.testing.assert_allclose(evaluate([2., 5., 4.], 1), [-3., 1., np.nan], equal_nan=True)


def test_dpo_missing_prices(evaluate):
    # Missing data invalidates full rolling windows and the displaced source.
    result = evaluate([2., 5., None, 7., 9., 18., 8., 11.], 4)
    np.testing.assert_allclose(result, [np.nan] * 3 + [-3.5, -2.5] + [np.nan] * 3, equal_nan=True)


@pytest.mark.parametrize("period", [0, -1])
def test_dpo_invalid_period(evaluate, period):
    with pytest.raises(ValueError, match="period must be greater than zero"):
        evaluate([1., 2., 3.], period)


def test_dpo_new_bars_fill_centered_tail(evaluate):
    before = evaluate([2., 5., 9., 7., 9., 18., 8.], 4)
    after = evaluate([2., 5., 9., 7., 9., 18., 8., 11.], 4)
    np.testing.assert_allclose(after[:4], before[:4])
    assert np.isnan(before[4])
    assert after[4] == pytest.approx(-2.5)
    assert np.isnan(after[-3:]).all()
