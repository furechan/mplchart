# Panes and axes — creation vs selection

Design note, July 2026. Records the analysis and decisions behind the pane/axes model. Status: **final model agreed and implemented 2026-07-26 (supersedes the earlier `_current_axes`/`set_axes` sketch); `target=` removals done 2026-07.**

## Vocabulary

- **pane** — the user-facing concept: an inner subplot in the vertical stack. Not a runtime type; a role certain Axes play.
- **axes** — the matplotlib object. The figure holds three kinds, discriminated by the `_label` attribute: the *root* axes (`"root"`, x-grid and title), *twinx* overlays (`"twinx"`, e.g. Volume), and the unlabeled inner subplots — only the last kind are panes.
- Client-facing parameter names are `position` (creation: `"above"`/`"below"`) and `pane` (selection: `"main"`, `"twinx"`). **`target` is internal jargon of the axes layer only** — it never appears in user-facing signatures.

## The problem (historical)

There was no explicit "current pane" state. The `"same"` target resolved to `axes[-1]` — the most recently **created** pane. Selection did not reorder that list; creation appended. So stickiness was an accident of creation:

- `LinePlot(target="below")` **leaked** — it created a pane and dragged every following indicator into it (unintended stickiness). Fixed 2026-07 by removing `target=` from the renderers and `plot()`.
- `Pane("main")` was a **silent no-op** — selection could not stick because only creation moved `axes[-1]`.

Both misbehaviors had one root cause: creation was sticky, selection could not be, and nothing in the API distinguished the two.

## The final model: disjoint verbs, no state

Stickiness is a property of the *type*, not of the argument:

- **`Pane(position="above"|"below")` / `chart.pane(position)` — creative and sticky, the only pane creator.** Every call creates a new pane; the new pane becomes current. Selecting values are rejected — `Pane("main")` is a loud `ValueError`, not a fixed behavior.
- **Renderer `pane="main"|"twinx"` (`LinePlot`, `AreaPlot`, `BarPlot`, `Bands`) — selective and ephemeral.** Places that one primitive; never moves the cursor. Creating values are rejected — a new pane is chart structure and structure is declared by `Pane`.

The vocabularies are **disjoint** — creation uses prepositions (`"above"`, `"below"`), selection uses locations (`"main"`, `"twinx"`; future `"top"`, `"bottom"`). The sticky/ephemeral question cannot be asked of the wrong object, and the parameter names (`position` vs `pane`) don't overlap either.

**No cursor state.** With selection stripped of stickiness, "current = last created" is *correct by construction* — `axes[-1]` is the current pane because nothing but creation can compete. The earlier design's underlying assumption is vindicated rather than replaced; `_current_axes`/`set_axes` (a previous iteration of this note) are unnecessary.

Rule of thumb: **`Pane` opens panes for what follows; `pane=` borrows an existing pane for one primitive.** A shared side pane is always spelled `Pane("above"), RSI(), ADX()`; a one-off overlay is `LinePlot(x, pane="main")`.

## Canvas layer

- **`get_axes(target=None)`** — selective, pure, never moves anything. `"same"` (default) → last-created pane; `"main"` → first pane; `"twinx"` → twin overlay of the current pane. Raises on `"above"`/`"below"` (pointing at `Pane`). One documented exception: resolving with no pane yet bootstraps the first pane (initialization, not movement — and for `"twinx"` the bootstrap returns the *plain pane*, see Volume below).
- **`new_axes(position="below", *, height_ratio=None)`** — the creative half, surfacing `layout.add_vplot` (which existed all along; `get_axes` used to reach down to it). Creates the pane; by list order it is immediately current. Name avoids matplotlib's `Figure.add_axes` (different meaning).

## The Volume special case (by design)

`Volume` always asks `get_axes("twinx")` and inspects the result's `_label`. The ownership rule lives in `get_axes` itself (moved there 2026-07-26): **an empty current pane resolves as its own overlay** — nothing to be scale-independent from — while a pane with content (`has_data()`) yields a fresh twin stamped `_label="twinx"`:

- current pane has content → twin → overlay etiquette: bars squashed into the bottom quarter (`set_ylim(0, 4*vmax)`), y-axis hidden.
- current pane empty (volume-only chart `chart.plot(Volume(sma=50))`, or right after `Pane("below")`) → the pane itself → Volume owns it: full height, visible scale. The second case is the classic dedicated volume sub-pane, which the old bootstrap-based detection could never produce (a pane *existed*, so it twinned the empty pane — also, `plot()` pre-bootstraps a pane for root-drawing primitives, so "no pane exists" was unobservable inside `plot()` anyway).

Known wrinkle (accepted, no action — decided 2026-07-26): when the pane has content, `get_axes("twinx")` creates a *new* twin every call (no reuse). No practical use case puts two twinx overlays on one pane (one `Volume()` per pane is the pattern), and reuse would raise a real semantic question (shared vs independent overlay scales) not worth deciding speculatively.

## Scope of `pane=`

Only the four indicator renderers: `LinePlot`, `AreaPlot`, `BarPlot`, `Bands`. Everything else keeps its hardwired discipline: price/chart-type renderers draw on the current pane (and Renko/PointFigure must be first anyway); `AutoPlot` is a dispatcher, not user-facing — no `pane=` at this stage; `Volume` has the twinx discipline; `Stripes`/`VLine` are root-layer; `Markers` pins to main (draws at close); `HLine` stays simple on the current pane. Primitives advance on demand, never as a sweep (the styling maturity-model doctrine applies).

## Future extensions (designed-for, not implemented)

- Selective vocabulary can grow freely without touching creation: `pane="top"` / `pane="bottom"` (visually extreme panes — genuinely new addressing: `"main"` is *first-created*, not topmost once `"above"` panes exist).
- If bulk return-to-a-prior-pane ever proves needed, letting `Pane` also select-and-stick is a backward-compatible escape valve. Until then, order the plot list so grouped content is contiguous; stragglers use `pane=`.

## Consequences (mostly landed 2026-07)

- `target=` removed from `plot()`/`LinePlot`/`AreaPlot`/`BarPlot` (done); reinstated as `pane=` with sound (ephemeral) semantics — not a flip-flop: the removal was of the broken accidental stickiness.
- `pane()` / `Pane` are trivial sugar over `new_axes` (+ yticks); the duplicated bodies go away.
- Grouping is explicit: `[Pane("below"), ROC(1), ROC(1) | EMA(20)]`. Adjacency-based coupling breaks on reorder and is invisible — exactly what was removed.

## Naming rationale

`pane()`, not `add_pane()`: the fluent chain reads as scoping, `add_*` conventionally returns the created object (this returns `self`), and finchart uses the same name. `new_axes`, not `add_axes`: matplotlib's `Figure.add_axes` means explicit-coordinate placement. `position`, not `target`, for creation: with only `"above"`/`"below"` left, the argument is a position in the vertical stack. `pane=`, not `target=`, for selection: it names the thing being selected in the user's vocabulary.
