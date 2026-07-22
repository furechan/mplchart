---
name: project-publish-readme-ordering
description: README edits must land before inv build — the wheel bakes pypi-readme in at build time
metadata:
  type: project
---

`inv build` regenerates `output/pypi-readme.md` from `README.md` and bakes it into the wheel. Any README content change made after `build` (even before `publish`) misses the published release — PyPI rejects re-uploads of the same version, so the fix only ships with the next one.

**Why:** publishing 0.0.40 (July 2026), the TrendLines README entry was added after `inv build`/`inv publish`, so the PyPI page for 0.0.40 shows the old readme.

**How to apply:** when a release includes README-worthy changes (new primitives/indicators, API changes), update `README.md` first, then run `inv check` → `inv build` → `inv publish` → `inv bump`.
