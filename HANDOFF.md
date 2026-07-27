# Handoff — styling / color cycles

Transient note for the next session (2026-07-27). Delete once the key-aliases work lands.

## Where things stand

The style system was surveyed against mplfinance and three gaps were closed in code (all shipped, tests green): directional candle wicks, `volume.use_prev_close`, and volume bar outlines. mplfinance's style model now maps in full for price renderers — verified across all 16 of its styles.

One thing is **designed but not implemented**: key aliases and the overlay cycle.

## Read these first

- **[notes/key-aliases.md](notes/key-aliases.md)** — the design to implement. Vocabulary (`name → prefix → alias → key`, with `facet`), where resolution lives (`get_setting` owns cycling, `resolve_color` owns color interpretation), cycle state (a `Counter` per axes with modulo indexing), and the rejected alternatives with reasons. Enough to start coding without re-deriving anything.
- **[notes/style-settings.md](notes/style-settings.md)** — the settings vocabulary and the **indicator styling doctrine**. Its "category mapping rejected" bullet (2026-07-23) is what key aliases reinstates; the revision and its grounds are recorded directly beneath it. Read both before touching cycle behavior.
- **[notes/styles-mismatch.md](notes/styles-mismatch.md)** — how mplfinance styles map onto ours, key by key, with usage counts across its 16 styles. Also the two traps found while implementing: retired `seaborn-*` sheet names, and `"none"` in a per-bar edge array rendering as semi-transparent black.

Related: [notes/themes-review.md](notes/themes-review.md) surveys what themes exist across matplotlib / morethemes / mplfinance / mplchart — background for GitHub issue #19 (platform themes: ThinkOrSwim, Bloomberg, ...). None of those exist in the Python plotting world; palettes would have to be sampled from screenshots.

## Next step

Implement key aliases per the note. Backlog entry is under **API** in [BACKLOG.md](BACKLOG.md).

## Loose ends

- **11 unpushed commits** at the time of writing — code plus notes. Pushing triggers the pages deploy.
- `pdoc` is still in dev deps but unused since the API reference moved to griffe.

## Working rule

**Check `notes/` before designing anything here.** A full design was worked out this session before discovering the doctrine in `style-settings.md` had already considered and rejected it. The notes are load-bearing, not archival.
