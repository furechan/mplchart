---
name: feedback-publish-smoke-test
description: Smoke-test the built wheel in an isolated env (latest deps) before publishing — the dev venv masks version-dependent breakage
metadata:
  type: feedback
---

Before `inv publish`, smoke-test the freshly built wheel in an isolated environment with unpinned (latest) dependencies:

```bash
uv run --no-project --isolated --with dist/mplchart-<ver>-py3-none-any.whl --with pandas python -c "<import + render a styled chart>"
```

**Why:** 0.0.41 (2026-07-24) shipped with `Chart()` crashing on matplotlib 3.11 — the dev venv had matplotlib 3.10.8 where `matplotlib.style.core` was still attribute-accessible; 3.11 removed the binding. All 538 tests passed locally; only the isolated-env smoke against the published wheel caught it (fixed in 0.0.42 within minutes).

**How to apply:** run the smoke between `inv build` and `inv publish`, exercising at least: default `Chart()`, a shipped style by name, a matplotlib sheet name, and `render()`. After publishing, verify once more installing from PyPI (`--no-cache --with "mplchart==<ver>"`; the index can lag ~15s). Prefer direct `from module.submodule import name` over parent-attribute access (`pkg.sub.attr`) for private-ish matplotlib internals — attribute bindings on parent packages are not stable across versions.
