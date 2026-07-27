# Key Aliases — and the overlay cycle

Design for a key-rename step in settings lookup, owned by the style. Flagship application: a shared color cycle for price-pane overlays (`sma`, `ema`, `hma`, ... drawing successive colors from one palette), which is what mplfinance's `mavcolors` does and what mplchart cannot express today.

Status: **designed, not implemented** (July 2026). Companion to [style-settings.md](style-settings.md) and [styles-mismatch.md](styles-mismatch.md).

Name note: "key alias" — not "style alias", which would read as an alias for a *style name* (morethemes names already resolve as styles). What gets renamed is the settings lookup key.

## The problem

Settings keys are derived from the indicator label: `resolve_color(get_label(indicator), ...)`, normalized by `extract_prefix` — `SMA(20)` → `sma`, and the polars `sma-20` → `sma` too, so the key is backend-stable. Good for *semantic* keys (`rsi`, `macdhist`, `bands`, `overbought`), which is what the settings vocabulary is for.

But it makes per-instance cycling useless. A list value cycles per key, so `{"sma.color": ["red", "blue", "green"]}` gives SMA(20)/SMA(50)/SMA(200) three colors — and `EMA(20)` falls out entirely, taking the matplotlib prop-cycle instead. To emulate mplfinance's mav palette you would duplicate the same list under `sma`, `ema`, `hma`, `wma`, `dema`, `tema`, `rma`, ... and custom indicators still escape it. Consequently **no shipped style uses a list value and the styler's cycle machinery is dormant** (verified 2026-07-27).

Cycles only mean something across a *semantic group*. A color for `overbought` or `macdhist` makes sense; a color for "SMA(20) specifically" does not — you put your moving averages in a sensible order (long to short) and let them cycle, which is exactly mplfinance's model.

## The mechanism

One verb per step, single lookup:

```
name "SMA(20)"  →  extract  →  key "sma"  →  alias  →  key "overlay"  →  lookup "overlay.color"
```

The alias is a **rename**, not a fallback chain: the pre-alias key is not tried. That keeps the model single-lookup and makes cycle keying correct by construction — the cycle is stored under the post-alias key, so `sma`, `ema` and `hma` share **one** cycle. (A candidate-chain design was considered and rejected: it needs "which candidate matched" bookkeeping to key the cycle correctly, and introduces a second grouping noun alongside "role".)

Placement: the rename belongs in `get_setting` (a key rename should apply wherever a key is looked up, all facets), with `resolve_color` inheriting it.

No primitive parameter. An earlier sketch added `role=`/`group=` to the renderers; dropped — the first argument was never a role (it is the indicator's label), and "role"/"group" are competing nouns for the same idea. `color=` already covers the one-off override, and the alias map covers the systematic case.

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
