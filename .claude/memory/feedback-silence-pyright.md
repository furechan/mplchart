---
name: Silence type checker with type: ignore, not runtime casts
description: Use # type: ignore[...] for false positives from ty/pyright; don't wrap in runtime casts
type: feedback
---

Use `# type: ignore[error-code]` to silence false positives from the type checker. Do not wrap values in runtime casts (e.g. `pd.DatetimeIndex(x)`) just to satisfy the type checker.

**Why:** Runtime casts add overhead and change behavior. `# type: ignore` is zero-cost and honest about what's happening.

**How to apply:** Add `# type: ignore[reportAttributeAccessIssue]` (or the relevant code) on the offending line. Use the specific error code when known rather than a bare `# type: ignore`.
