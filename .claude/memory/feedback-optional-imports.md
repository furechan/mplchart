---
name: Optional imports in tests
description: Use pytest.importorskip for optional test dependencies, not try/except with None fallback
type: feedback
---

Use `pytest.importorskip("module")` instead of the try/except pattern for optional deps in tests.

**Why:** The try/except + `= None` fallback causes type checker false positives and is less idiomatic pytest. `importorskip` returns the module directly (correct type), skips the whole file if unavailable, and requires no `# type: ignore`.

**How to apply:** Put normal imports first, then `x = pytest.importorskip("x")` after them (avoids ruff E402). Split optional-dep tests into their own file so the skip applies to the whole module.
