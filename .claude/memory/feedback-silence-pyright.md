---
name: Silence type checker with type: ignore, not runtime casts
description: Use # type: ignore[...] for false positives from ty/pyright; don't wrap in runtime casts
type: feedback
---

Use `# type: ignore[error-code]` to silence false positives from the type checker. Do not wrap values in runtime casts (e.g. `pd.DatetimeIndex(x)`) just to satisfy the type checker.

**Why:** Runtime casts add overhead and change behavior. `# type: ignore` is zero-cost and honest about what's happening.

**How to apply:** Add `# type: ignore[reportAttributeAccessIssue]` (or the relevant code) on the offending line. Use the specific error code when known rather than a bare `# type: ignore`.

When only Pylance/pyright complains and `ty` (the project checker) passes, use a checker-private `# pyright: ignore[rule]` instead: `ty` treats a bare `# type: ignore` as its own suppression directive and emits `unused-type-ignore-comment` warnings when it sees no error on that line, while it ignores `# pyright:` comments as plain text. (Established 2026-07 on the `pandas.api.typing.Expression` import — Pylance's bundled pandas-stubs predate the symbol.)

When BOTH ty and pyright complain, `# type: ignore[<ty-rule>]` does NOT suppress ty (observed 2026-07: `# type: ignore[invalid-argument-type]` left the ty error standing). Use both checker-private directives on the line: `# ty: ignore[rule]  # pyright: ignore[rule]` (e.g. `# ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]` on `PolyCollection(verts=...)` ndarray verts).
