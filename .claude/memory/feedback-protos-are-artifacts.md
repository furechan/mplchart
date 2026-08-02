---
name: feedback-protos-are-artifacts
description: playground proto notebooks are frozen design artifacts — self-contained by design, never retrofitted to import from src
metadata:
  type: feedback
---

Prototype notebooks in `playground/prototypes/` (`renko-proto.ipynb`, `pnf-proto.ipynb`, `trend-lines-proto.ipynb`, ...) deliberately define their own local copies of calcs and helpers. Do not propose slimming them to import from src, and do not update them when the src versions evolve — they are the historical record of how a design was derived, not maintained examples.

**Why:** the user rejected a backlog item to retrofit renko/pnf protos onto src imports (2026-07-26): "no, these are protos." Maintained, user-facing notebook content lives in `examples/` and `docs/` ([[project-examples-structure]]).

**How to apply:** when a prototype's design ships to src, the proto stays as-is (its Findings cell records the journey); new demonstrations of the shipped feature go in the gallery or tutorials, not back into the proto.
