---
name: project-pane-model
description: pane model — Pane(position=) creative+sticky is the only creator; renderer pane= selective+ephemeral; no cursor state; design in notes/axes-stickiness.md
metadata:
  type: project
---

Panes follow a strict creation/selection split (shipped 2026-07-26; full design in `notes/axes-stickiness.md`):

- `Pane(position="above"|"below")` / `chart.pane(position)` — **creative and sticky, the only pane creators**. Every call opens a new pane; the new pane becomes current. Selecting values (`"main"`) raise.
- Renderer `pane="main"|"twinx"` on `LinePlot`/`AreaPlot`/`BarPlot`/`Bands` — **selective and ephemeral**: places that one primitive, never moves the current pane. Creating values raise. `AutoPlot` deliberately has no `pane=` (dispatcher, not user-facing).
- **No cursor state** — current = last-created pane (`axes[-1]`), correct *by construction* because selection can't stick. Do not add `_current_axes`-style state; the disjoint vocabularies (prepositions create, locations select) carry the design.
- Canvas: `get_axes(target)` selective-only, `new_axes(position=)` the creator, `panes()` accessor; `target` is internal jargon — client-facing names are `position` and `pane`.
- The `"twinx"` target resolves an *empty* current pane as itself (the ownership rule lives in `get_axes`, not Volume): volume-only charts and `[..., Pane("below"), Volume()]` dedicated sub-panes render full-height; a pane with content yields a fresh twin, and `ax._label == "twinx"` drives Volume's squash.
- Reserved extensions (in the note): selective `"top"`/`"bottom"`; `Pane` select-and-stick as a backward-compatible escape valve if bulk return-to-pane ever proves needed.

**Why:** the old model had accidental stickiness (creation leaked via `axes[-1]`, `Pane("main")` was a silent no-op). The user drove the final model through several iterations — the `_current_axes`/`set_axes` sketch in earlier revisions of the note was superseded before implementation.
