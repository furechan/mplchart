---
name: project-python-version-skew
description: local venv is Python 3.11 but GitHub CI tests on 3.12/3.13 — version-sensitive code passes locally and fails only in CI
metadata:
  type: project
---

The project venv (`.venv`) runs Python 3.11 while the GitHub "Python package" workflow tests on newer versions (3.12/3.13 as of 2026-08). Code relying on behavior changed in 3.12+ passes the full local suite and fails only on CI.

**Why:** bit in 2026-08 — `test_provider_packages_have_zero_blast_radius` used a legacy `find_module`/`load_module` meta-path finder, which the import system stopped consulting in Python 3.12; the block silently no-oped on CI (3.13) while working locally on 3.11. Fixed with the modern `find_spec` API (raise `ImportError` from it to block).

**How to apply:** after pushing, check `gh run list`; for anything touching import machinery, deprecated stdlib APIs, or version-gated behavior, verify on a newer interpreter locally first — `uv run --python 3.13 --no-project python -c "..."` works for isolated mechanics without installing the project.
