---
name: Silence pyright with type: ignore, not runtime casts
description: Don't wrap values in runtime casts (e.g. pd.DatetimeIndex()) just to satisfy pyright — use type: ignore instead
type: feedback
---

Use `typing.cast(T, x)` to silence pyright false positives when the correct type is known. Prefer it over `# type: ignore` and over runtime casts like `pd.DatetimeIndex(x)`.

**Why:** `typing.cast` is a zero-cost pure type hint (no-op at runtime), cleaner than ignore comments, and avoids unnecessary runtime overhead.

**How to apply:** `cast(pd.DatetimeIndex, prices.index).tz_localize(None)` — wrap the expression in `cast(TargetType, value)` then access the method.
