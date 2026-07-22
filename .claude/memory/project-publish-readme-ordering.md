---
name: project-publish-readme-ordering
description: README edits must land before inv build — the wheel bakes README.md in at build time
metadata:
  type: project
---

`inv build` bakes `README.md` directly into the wheel as the PyPI long description (`readme = "README.md"` in pyproject). The former generation step — `scripts/process-readme.py` producing `output/pypi-readme.md` — was removed in July 2026; README links are now absolute URLs (`https://github.com/furechan/mplchart/raw/main/...`) so they render on PyPI without rewriting. Any README content change made after `build` (even before `publish`) misses the published release — PyPI rejects re-uploads of the same version, so the fix only ships with the next one.

**Why:** publishing 0.0.40 (July 2026), the TrendLines README entry was added after `inv build`/`inv publish`, so the PyPI page for 0.0.40 shows the old readme.

**How to apply:** when a release includes README-worthy changes (new primitives/indicators, API changes), update `README.md` first, then run `inv check` → `inv build` → `inv publish` → `inv bump`. Keep README image/asset links absolute.
