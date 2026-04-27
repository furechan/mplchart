---
name: Backend architecture (pandas/polars split)
description: Core is backend-agnostic; pandas and polars each live in opt-in modules with matching extras
type: project
---

The package is architected as a backend-agnostic core with backend-specific opt-in modules. Core deps have neither pandas nor polars.

**Backend-agnostic core (no pandas/polars at import):** `chart`, `mapper`, `primitives`, `samples`, `utils` — pandas/polars are imported lazily only on the matching code path. (`plotters.py` was removed in 0.0.33; logic moved into `AutoPlot.plot_handler`.)

**Pandas-only modules (opt-in via `[pandas]` extra):** `indicators`, `library`, `pandas` — top-level `import pandas`, meant to be used only if pandas is installed.

**Polars-only modules (opt-in via `[polars]` extra):** `expressions/` subpackage — top-level `import polars`.

**Why:** Users pick the backend they want; installing mplchart without pandas should still give a working chart pipeline with the polars path. Mirrors the pattern `mplchart[polars]` already uses. The pandas-side hard imports are acceptable because `indicators`/`library` may eventually move to mintalib/barcalc and the problem goes away.

**How to apply:**
- Never add `import pandas` or `import polars` at module top in core files. Lazy-import inside the branch that needs it (see `mapper.slice_pandas`, `samples._load_pandas`).
- Test files are split per backend and named `test_<topic>_pandas.py` / `test_<topic>_polars.py`. Each file gates at the top with `pytest.importorskip("pandas")` or `pytest.importorskip("polars")`. Imports from mplchart modules that drag in the backend must come *after* the importorskip, suffixed with `# noqa: E402`.
- `pyproject.toml`: pandas and polars are both optional extras (no pandas in `dependencies`). Flipped.
- `tox.toml` has `[env.pandas]` (extras=pandas) and `[env.polars]` (extras=polars) envs for isolated backend testing — these are the regression fence against accidental hard imports. The Python-version envs (3.10–3.14) install both extras via `env_run_base` and run the full suite.
- Any core module added later (e.g. a new primitive) must not `from ..library import ...` — put shared helpers in `utils.py` (see how `calc_price` was moved there).
