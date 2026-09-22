---
name: feedback-run-pytest
description: Always run pytest after each fix or refactoring step
metadata:
  type: feedback
---

Run `uv run pytest` after each fix or refactoring, not just at the end.

**Why:** Catch regressions immediately rather than accumulating them across multiple changes.

**How to apply:** After every Edit/fix, run pytest before moving on to the next error.
