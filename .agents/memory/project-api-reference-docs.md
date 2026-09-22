---
name: project-api-reference-docs
description: API reference pages are generated committed markdown (griffe-based script); griffe2md and mkdocstrings were evaluated and rejected — committed md is a deliverable for agents
metadata:
  type: project
---

`docs/reference/{chart,primitives,indicators,expressions,styles}.md` are **generated** — never hand-edit; regenerate with `inv apidocs` (`scripts/make-api-docs.py`) after docstring changes. The script uses griffe (static extraction, google docstrings → structured sections) and renders all markdown itself, with a built-in render check (parses each page with mkdocs' markdown extensions; fails on trapped lists / unbalanced fences).

**Why this design (July 2026 evaluation):** committed readable markdown is itself a deliverable — for git diffs and for AI agents — not just an intermediate for the HTML site. mkdocstrings was rejected (HTML-only output, no committed pages). griffe2md was piloted and rejected: default output 7.5x bloat, Examples sections render broken without reforming docstrings to doctest style, dead base-class anchors. A first pdoc-based version worked but needed regex patches to convert pdoc's internal markdown dialect to python-markdown — griffe's structured sections eliminated that whole layer.

Full decision record and roadmap (discovery layer / llms.txt plan, rejected alternatives, mintalib port, layout ladder): `notes/api-reference-roadmap.md`.

Notes: docstring prose may use RST-isms (``x``, :func:`y`) — the script converts them. Module docstrings become page intros. `mplchart.primitives` has a curated `__all__` (page order); indicators' dynamic `__all__` falls back to source order. pdoc is still in dev deps but unused by the script (predates this work — owner's call to remove). Same approach portable to mintalib (stubs + inspection fallback for the Cython core), copy-first, package later if drift hurts. Related: [[project-examples-structure]].
