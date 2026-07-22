# Axes stickiness — Pane vs axes, current-pane semantics

Design note, July 2026. Records the analysis and decisions behind the pane/axes cleanup. Status: **agreed; `target=` removals done, `_current_axes` / `set_axes` split pending**.

## Vocabulary

- **pane** — the user-facing concept: an inner subplot in the vertical stack. Not a runtime type; a role certain Axes play.
- **axes** — the matplotlib object. The figure holds three kinds: the *root* axes (label `"root"`, x-grid and title), *twinx* overlays (label `"twinx"`, e.g. Volume), and the unlabeled inner subplots — only the last kind are panes.
- Docstrings and user API say *pane*; code-level methods and attributes say *axes* (`get_axes`, `_current_axes`). The bridge sentence: `pane()` selects or creates a pane and makes its axes current; indicators draw on the current axes.

## The problem

There is no explicit "current pane" state. The `"same"` target resolves to `axes[-1]` — the most recently **created** pane in figure order. Selection does not reorder that list; creation appends to it. So stickiness is an accident of creation:

| | creates a pane (`"above"`/`"below"`) | selects existing (`"main"`, `"same"`) |
|---|---|---|
| `LinePlot(target=...)` | **leaks** — followers move to the new pane (unintended) | scoped, correct |
| `Pane` / `.pane()` | works — followers move (intended) | **doesn't stick** — silent no-op (broken) |

Verified empirically: `chart.plot([Candlesticks(), Pane("below"), RSI(), Pane("main"), EMA(10)])` puts the EMA in the RSI pane — `Pane("main")` is a silent no-op. Conversely `SMA(20) @ LinePlot(target="below")` drags the next indicator into the SMA's new pane. Both cells that misbehave do so for the same root cause: "current" is derived from creation order, so creation is sticky and selection cannot be.

Nobody hit the `Pane("main")` bug because all notebook uses are `"below"`/`"above"` — the cells where the accident happens to do the right thing.

## The decision

Resolve the ambiguity at the axes-management level — not by having `pane()`/`Pane` poke chart state from above. `Chart` gains explicit current-axes state and a getter/setter split:

```python
_current_axes = None   # the current pane's axes; never root/twinx
```

- **`get_axes(target=None) -> Axes`** — pure resolver, never moves the cursor. `"same"` → current axes; `"main"` → first pane; `"twinx"` → twin of current. Creating targets (`"above"`/`"below"`) are **not accepted** — creation is inherently cursor-relevant. One documented exception: resolving `"same"` with no pane yet bootstraps the first pane and makes it current (initialization, not movement — there is nothing to preserve).
- **`set_axes(target=None, *, height_ratio=None) -> Axes`** — resolver + cursor move. Accepts all targets including `"above"`/`"below"`, records the result as current, returns it. Name echoes matplotlib's `sca` (set current axes).
- **`set_axes("twinx")` raises** — a twin is a y-scale overlay, not a pane; the invariant *current axes is always a pane* is enforced by the only writer. Overlays go through `get_axes("twinx")`.

The rule becomes structural rather than conventional: **`get_axes` answers questions; `set_axes` changes the answer. Creation is always sticky, and only `set_axes` creates.** The sticky/punctual ambiguity is unrepresentable.

## Consequences

- `pane()` / `Pane` become trivial sugar over `set_axes` (+ yticks); the duplicated body goes away, and `Pane("main")` starts working.
- The `target=` parameter is **removed** from `LinePlot`/`AreaPlot`/`BarPlot` (zero usage anywhere). The user vocabulary shrinks to *pane*; `target` survives only as internal jargon in the axes layer. Punctual placement for custom primitives is `chart.get_axes(...)`; punctual pane *creation* is intentionally impossible.
- `plot(target=...)` is **removed** (superseded by `pane()`, zero usage; the memory records that migration).
- Grouping is explicit: to put ROC and its EMA in one pane, write `[Pane("below"), ROC(1), ROC(1) | EMA(20)]`. Adjacency-based coupling ("the next line inherits my pane because I happened to create one") is exactly what is being removed — it breaks on reorder and is invisible in the code.

## Naming rationale

`_current_axes`, not `_current_pane`: the attribute holds what `get_axes()` returns — a matplotlib Axes — and `return self._current_pane` inside `get_axes` would mix the vocabularies at the code level. The pane invariant (never root/twinx) doesn't need the name; it lives in the write discipline (`set_axes` is the only writer, and it rejects twins) and a comment.

`pane()`, not `add_pane()`: the method selects as often as it creates ("create or select"), `add_*` in matplotlib conventionally returns the created object (this returns `self` for chaining), the fluent chain reads as scoping, and finchart uses the same name with the same contract.
