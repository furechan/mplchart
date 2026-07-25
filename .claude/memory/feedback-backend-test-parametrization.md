---
name: feedback-backend-test-parametrization
description: backend-agnostic features get one test file parametrized over both backends, not module-gated splits
metadata:
  type: feedback
---

When testing backend-agnostic code (works with both pandas and polars), put all its tests in one file parametrized over backends — do not gate the module on one backend and scatter the other backend's coverage elsewhere.

**Why:** the user rejected a layout where `test_heikinashi.py` was pandas-gated with the polars calc test moved to `test_polars_primitives.py`: "HeikinAshi is backend agnostic same as candlesticks... polars pandas same treatment." A module-level `pytest.importorskip("pandas")` silently skips every test in the file — including polars tests — on polars-only installs.

**How to apply:** use a params fixture so each backend variant runs or skips independently:

```python
@pytest.fixture(params=["pandas", "polars"])
def backend(request):
    pytest.importorskip(request.param)
    return request.param

@pytest.fixture
def prices(backend):
    return sample_prices(freq="daily", backend=backend)
```

Keep backend-specific asserts behind `if backend == "pandas":` (e.g. index preservation). Module-level importorskip is only for genuinely single-backend files ([[feedback-optional-imports]]). Verify with `tox -e pandas,polars` that each single-backend env actually runs the tests.
