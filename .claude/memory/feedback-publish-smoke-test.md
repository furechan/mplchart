---
name: feedback-publish-smoke-test
description: Test the built wheel outside the dev environment before publishing — the dev venv masks version-dependent breakage
metadata:
  type: feedback
---

The release workflow builds the wheel and installs it into separate environments for every supported Python version before publishing. For additional local coverage against unpinned (latest) dependencies, smoke-test a local wheel with:

```bash
uv run --no-project --isolated --with dist/mplchart-<ver>-py3-none-any.whl --with pandas python -c "<import + render a styled chart>"
```

**Why:** 0.0.41 (2026-07-24) shipped with `Chart()` crashing on matplotlib 3.11 — the dev venv had matplotlib 3.10.8 where `matplotlib.style.core` was still attribute-accessible; 3.11 removed the binding. All 538 tests passed locally; only the isolated-env smoke against the published wheel caught it (fixed in 0.0.42 within minutes).

**How to apply:** use the GitHub Actions release workflow to build, test, and publish the wheel. When doing an extra local smoke test, exercise at least: default `Chart()`, a shipped style by name, a matplotlib sheet name, and `render()`. After publishing, verify once more installing from PyPI (`--no-cache --with "mplchart==<ver>"`; the index can lag ~15s). Prefer direct `from module.submodule import name` over parent-attribute access (`pkg.sub.attr`) for private-ish matplotlib internals — attribute bindings on parent packages are not stable across versions.
