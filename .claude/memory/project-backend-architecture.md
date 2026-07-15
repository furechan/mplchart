---
name: Backend architecture (pandas/polars split)
description: Core is backend-agnostic; pandas and polars each live in opt-in modules with matching extras
type: project
---

The package is architected as a backend-agnostic core with backend-specific opt-in modules. Core deps have neither pandas nor polars.

**Backend-agnostic core (no pandas/polars at import):** `chart`, `mapper`, `primitives`, `model.primitive`, `samples`, `utils` — pandas/polars are imported lazily only on the matching code path. (`plotters.py` was removed in 0.0.33; logic moved into `AutoPlot.plot_handler`.)

**Pandas-only modules (opt-in via `[pandas]` extra):** `indicators`, `library`, `pandas`, `model.indicator` — top-level `import pandas`, meant to be used only if pandas is installed.

**Polars-only modules (opt-in via `[polars]` extra):** `expressions/` subpackage — top-level `import polars`.

**`model/` is a namespace package** (mirrors mintalib's layout): `__init__.py` is intentionally empty — no re-exports. Consumers import from the specific submodule: `from ..model.primitive import BindingPrimitive`, `from .model.indicator import Indicator`. This keeps the pandas-only `Indicator` class out of the backend-agnostic primitive import chain.

**Why:** Users pick the backend they want; installing mplchart without pandas should still give a working chart pipeline with the polars path. Mirrors the pattern `mplchart[polars]` already uses. The pandas-side hard imports are acceptable because `indicators`/`library` may eventually move to mintalib/barcalc and the problem goes away.

**How to apply:**
- Never add `import pandas` or `import polars` at module top in core files. Lazy-import inside the branch that needs it (see `mapper.slice_pandas`, `samples._load_pandas`).
- Test files are split per backend and named `test_<topic>_pandas.py` / `test_<topic>_polars.py`. Each file gates at the top with `pytest.importorskip("pandas")` or `pytest.importorskip("polars")`. Imports from mplchart modules that drag in the backend must come *after* the importorskip, suffixed with `# noqa: E402`.
- `pyproject.toml`: pandas and polars are both optional extras (no pandas in `dependencies`). Flipped.
- `noxfile.py` has `pandas` (pandas-only install) and `polars` (polars-only install) sessions for isolated backend testing — these are the regression fence against accidental hard imports. The `matrix` sessions (Python 3.10–3.14, tag `full`) install both backends and run the full suite.
- Any core module added later (e.g. a new primitive) must not `from ..library import ...` — put shared helpers in `utils.py` (see how `calc_price` was moved there).
