---
name: project-backend-architecture
description: Core is backend-agnostic; pandas and polars each live in opt-in modules with matching extras
metadata:
  type: project
---

The package is architected as a backend-agnostic core with backend-specific opt-in modules. Core deps have neither pandas nor polars.

**Backend-agnostic core (no pandas/polars at import):** `chart`, `dataview`, `primitives`, `model.primitive`, `samples`, `utils`, `styles` — pandas/polars are imported lazily only on the matching code path. (`plotters.py` was removed in 0.0.33; `mapper` was replaced by `dataview.py` — `chart.mapper` survives as a deprecated alias for `chart.view`.)

**Pandas-only modules (opt-in via `[pandas]` extra):** `indicators`, `library`, `pandas`, `model.indicator` — top-level `import pandas`, meant to be used only if pandas is installed.

**Polars-only modules (opt-in via `[polars]` extra):** `expressions/` subpackage — top-level `import polars`.

**`model/` is a namespace package** (mirrors mintalib's layout): `__init__.py` is intentionally empty — no re-exports. Consumers import from the specific submodule: `from ..model.primitive import BindingPrimitive`, `from .model.indicator import Indicator`. This keeps the pandas-only `Indicator` class out of the backend-agnostic primitive import chain.

**Why:** Users pick the backend they want; installing mplchart without pandas should still give a working chart pipeline with the polars path. Mirrors the pattern `mplchart[polars]` already uses. The pandas-side hard imports are acceptable because `indicators`/`library` may eventually move to mintalib/barcalc and the problem goes away.

**How to apply:**
- Never add `import pandas` or `import polars` at module top in core files. Lazy-import inside the branch that needs it (see the per-backend views in `dataview.py`, `samples`; `utils.wrap_result` uses `sys.modules` — never imports at all).
- Backend-*specific* test suites are split per backend (`test_pandas_*.py` / `test_polars_*.py`), gated at the top with `pytest.importorskip(...)`; imports from mplchart modules that drag in the backend come *after* the skip, suffixed `# noqa: E402`. Backend-*agnostic* features get ONE test file parametrized over both backends instead — see [[feedback-backend-test-parametrization]].
- `pyproject.toml`: pandas and polars are both optional extras (no pandas in `dependencies`). Flipped.
- `tox.toml` has `pandas` (pandas-only install) and `polars` (polars-only install) environments for isolated backend testing — the regression fence against accidental hard imports (`tox -e pandas,polars`; superseded `noxfile.py`). The `full` label runs Python 3.10–3.14 with both backends.
- Any core module added later (e.g. a new primitive) must not `from ..library import ...` — put shared helpers in `utils.py` (see how `calc_price` was moved there).
