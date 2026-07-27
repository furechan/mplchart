# Key Aliases — and the overlay cycle

Design for a key-rename step in settings lookup, owned by the style. Flagship application: a shared color cycle for price-pane overlays (`sma`, `ema`, `hma`, ... drawing successive colors from one palette), which is what mplfinance's `mavcolors` does and what mplchart cannot express today.

Status: **designed, not implemented** (July 2026). Companion to [style-settings.md](style-settings.md) and [styles-mismatch.md](styles-mismatch.md).

This reinstates the "category mapping" that the 2026-07-23 doctrine in [style-settings.md](style-settings.md) rejected. That rejection was correctly reasoned on what was known then; the grounds for revisiting are recorded there and summarised below (the prop cycle cannot carry two palettes, and the identity-keyed reserve mechanism is not serializable).

Name note: "key alias" — not "style alias", which would read as an alias for a *style name* (morethemes names already resolve as styles). What gets renamed is the settings lookup key.

## The problem

Settings keys are derived from the indicator label: `resolve_color(get_label(indicator), ...)`, normalized by `extract_prefix` — `SMA(20)` → `sma`, and the polars `sma-20` → `sma` too, so the key is backend-stable. Good for *semantic* keys (`rsi`, `macdhist`, `bands`, `overbought`), which is what the settings vocabulary is for.

But it makes per-instance cycling useless. A list value cycles per key, so `{"sma.color": ["red", "blue", "green"]}` gives SMA(20)/SMA(50)/SMA(200) three colors — and `EMA(20)` falls out entirely, taking the matplotlib prop-cycle instead. To emulate mplfinance's mav palette you would duplicate the same list under `sma`, `ema`, `hma`, `wma`, `dema`, `tema`, `rma`, ... and custom indicators still escape it. Consequently **no shipped style uses a list value and the styler's cycle machinery is dormant** (verified 2026-07-27).

Cycles only mean something across a *semantic group*. A color for `overbought` or `macdhist` makes sense; a color for "SMA(20) specifically" does not — you put your moving averages in a sensible order (long to short) and let them cycle, which is exactly mplfinance's model.

## Vocabulary (settled 2026-07-27)

Five terms, no synonyms, each tied to a concrete step. **"Role" is retired here** — it was a competing noun for the same idea and earned nothing that `prefix` does not.

| term | example | what it is |
|---|---|---|
| `name` | `"SMA(20)"`, `"sma-20"`, `"candle.up"` | what the caller passes: an indicator label or an already-canonical prefix. Not `label` — that word means legend text (`LinePlot(label=...)`, `get_label`). |
| `prefix` | `"sma"`, `"candle.up"` | `extract_prefix(name)` — everything before the facet. Dots do not split, so a prefix may carry a variant (`candle.up`). |
| alias | `"sma"` → `"overlay"` | the style-owned rename applied to the prefix. A mapping, not a thing. |
| `facet` | `"color"`, `"alpha"` | the trailing segment, never sanitized. |
| `key` | `"overlay.color"` | prefix + facet — what indexes `settings`. |

```
name "SMA(20)"  →  extract  →  prefix "sma"  →  alias  →  prefix "overlay"  →  + facet  →  key "overlay.color"
```

## The mechanism

The alias is a **rename**, not a fallback chain: the pre-alias prefix is not tried. That keeps the model single-lookup and makes cycle keying correct by construction — the counter is stored under the post-alias prefix, so `sma`, `ema` and `hma` share **one** cycle. (A candidate-chain design was considered and rejected: it needs "which candidate matched" bookkeeping to key the cycle correctly, and introduces a second grouping noun.)

No primitive parameter. An earlier sketch added `role=`/`group=` to the renderers; dropped — the first argument was never a role (it is the indicator's name), and those were competing nouns for the same idea. `color=` already covers the one-off override, and the alias map covers the systematic case.

### Where the resolution lives

`get_setting` owns value resolution end to end — name → prefix → alias → key → lookup, **including cycling** when the value is a list. `resolve_color` keeps only color *interpretation* on whatever comes back: `~` snapping, the `line`/`fill` sentinels, hex normalization.

This split is forced, not stylistic: once `get_setting` resolves the key, `resolve_color` no longer knows what to key the counter on, and duplicating the walk in both would defeat the point of centralizing it. The cut is also cleaner than today's — one method resolves *what the setting is*, the other *what it means as a color* — and it makes cycling available to every facet instead of being a color-only privilege.

Cost, named honestly: `get_setting` grows an `ax` parameter used solely for counter keying, which is an odd thing for a settings lookup to take. Accepted — the alternative is exposing a `resolve_key` helper and walking twice.

### Cycle state

A `Counter` per axes, keyed by post-alias prefix, with modulo indexing — the shape of the original 2026-07 design (`count % len(colors)`), restored:

```python
self.counters = WeakKeyDictionary()   # ax -> Counter(prefix -> uses)
```

- **Keyed by axes, not styler-wide.** A prebuilt `Styler` passes through `get_styler` by identity and can be shared across charts (verified), so styler-level counters would leak chart 1's position into chart 2.
- **Counter, not `itertools.cycle`.** An int is inspectable when debugging why the third overlay came out wrong, restartable, and re-reads the palette each time so it cannot go stale against a changed list. The cycle-object leaves are opaque on all three counts.
- **`ax=None` raises** if the value is a list. Every real call site passes axes today; the only consumer is colors. Raising is loud, defers the question until someone actually needs it, and retires the `_NoAxes` sentinel class — which exists purely because `None` is not weakly referenceable.
- **Wrap, do not fall through to the prop cycle.** `tradingview` ships `mavcolors = ['#2962ff', '#2962ff']` — two identical blues, deliberately, so every MA renders alike. Wrapping preserves that intent for any number of overlays; falling through would hand the third overlay an unrelated color and silently break the style's meaning. Wrapping is also the ecosystem convention (matplotlib's prop cycle wraps; mpf uses `itertools.cycle`).

## Why not identity-keyed cycles

The alternative held in reserve by the 2026-07-23 doctrine was to key cycles on `id(value)`, so a style shares one palette by binding one list object to several prefixes:

```python
overlay = ["red", "blue", "green"]
settings = {"sma.color": overlay, "ema.color": overlay}   # the same object
```

Attractive — no new vocabulary, no resolution hop. Rejected 2026-07-27 on **serializability**: the grouping lives in the object graph, so a JSON/TOML round-trip turns one shared list into two equal-but-distinct ones and the sharing silently evaporates, leaving a style that reads byte-identical and behaves differently. It also breaks the shipped-style convention (`# pure data, zero imports`) by making a style file a small program whose variable bindings carry meaning.

Aliases stay declarative string→string data — serializable, diffable, schema-able, and legible to someone who has never seen the implementation.

## Ownership: aliases ship with the style

There is **no library-wide default alias map**. Each style declares its own, or none. `aliases` becomes a third mapping in the `Style` spec alongside `rc` and `settings` — static style data, same shape.

| style source | aliases | cycles |
|---|---|---|
| raw matplotlib stylesheets | none | one (`axes.prop_cycle`) |
| morethemes | none | one |
| converted mplfinance | `sma`, `ema` → `overlay` (forced by the conversion) | two: prop_cycle + `overlay.color` |
| mplchart's own styles | whatever each declares, possibly none | one or two, per style |

Only the mplfinance conversion path *needs* forced aliases, because its model assumes them.

This is what makes the design safe: today's shipped styles declare no aliases, so nothing changes for them. The overlay cycle comes alive only when a style provides both an alias map and a list-valued `overlay.color` — fully opt-in, zero regression surface.

It also resolves the shadowing question without machinery. Under an unconditional rename, a style that aliases `ema → overlay` and also sets `ema.color` gets a silent no-op. But since aliases ship with the style, the alias sits a few lines from the setting it shadows, in the same file — self-inflicted and locally visible. No eager validation needed (an earlier proposal, dropped as over-engineering).

Residual case, documented rather than validated: a *user* passing settings on top of an aliasing style (`Chart(style={"stylesheet": <mpf-derived>, "settings": {"ema.color": "red"}})`) can still be shadowed, since aliases and settings are no longer co-located. The diagnosis is to read the style's aliases.

## Why this closes the mplfinance cycle gap

mplfinance runs two cycles: `mavcolors` (explicit, moving averages only, outside rcParams) and the base stylesheet's `axes.prop_cycle` (untouched, everything else) — see [styles-mismatch.md](styles-mismatch.md). Converting `mavcolors` onto `axes.prop_cycle` is lossy: it always replaces a cycle mpf would have kept (the mav palette never equals the sheet cycle, 0/16).

With key aliases the conversion becomes structurally isomorphic:

- `mavcolors` → `overlay.color` (list)
- aliases `{"sma": "overlay", "ema": "overlay"}`
- `axes.prop_cycle` left alone

Two cycles on each side, doing the same jobs. The last approximation in the mismatch table becomes a real mapping.

## Vocabulary

Start with `overlay` alone — the one group with a proven use case and a direct mav mapping. Let `oscillator` / `signal` or anything else arrive with demand rather than being seeded speculatively.
