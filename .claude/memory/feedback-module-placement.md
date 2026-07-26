---
name: feedback-module-placement
description: low-level domain helpers get their own module (arrays.py, datetimes.py, colors.py) — utils.py is for general use only
metadata:
  type: feedback
---

Low-level helpers grouped by the thing they operate on get their own module — `arrays.py` (numpy array utilities), `datetimes.py`, `colors.py` — following the plural-noun-of-the-subject naming pattern. `utils.py` is reserved for general-purpose helpers.

**Why:** the user rejected placing `forward_fill` in `utils.py` (2026-07-26): "I want low level numpy stuff in their own module. utils is for general use."

**How to apply:** before adding a helper to `utils.py`, check whether a subject module exists or is warranted. Candidates for future migration out of utils: the numpy-boundary converters (`col_to_numpy`, `xvalues_to_float`) could move to `arrays.py` — don't move them speculatively, but new array-level helpers go there.
