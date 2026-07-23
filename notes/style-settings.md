# Style Settings — Candidate Vocabulary

Working list (2026-07-22) of settings keys we are entertaining for the [styler-sketch.md](styler-sketch.md) grammar `<role>[.<variant>].<facet>`. Sourced two ways: everything mplfinance exposes through its style system (full accounting at the bottom), and every styling parameter our own primitives expose today. Candidate list, not a commitment — roles land with the primitive retrofit.

## Naming rules

- Roles are singular nouns in mplchart lingo: `candle`, `ohlc`, `volume`, `hline`, `trendline` (note: supersedes the plural `candles.*` spellings in earlier sketch drafts). Deliberate exception: `wicks` — collective noun for the wick LineCollection, no variant.
- Variants: `up` / `down` / `off` for direction-colored elements (settled 2026-07-23: `down`, not `dn` — the kwargs keep `colorup`/`colordn`; `off` for the hollow-body fill, freeing `candle.hollow` for the future bool mode flag); element names (`ma`, `support`, `resistance`) where the role has sub-elements.
- Candle body outlines are their own role, not a variant: `edge.up.color` / `edge.down.color`.
- Facets: `color`, `alpha`, `width`, `linestyle` — always explicit, always last.
- Indicator roles are the `extract_prefix` names (`sma`, `macd`, `rsi`, …) — open-ended, not enumerated here.

Candlestick scheme taxonomy (mono hollow, two-color filled, yahoo-style, colored hollow) and the six-color renderer mapping: [candlestick-styles.md](candlestick-styles.md).

## Price / volume renderers

| Key | Consumer | Today's parameter / default | mplfinance |
|---|---|---|---|
| `candle.up.color` | Candlesticks | `colorup` / `text.color` | `marketcolors.candle.up` |
| `candle.down.color` | Candlesticks | `colordn` / `text.color` | `marketcolors.candle.down` |
| `candle.off.color` | Candlesticks | hollow-body fill / `axes.facecolor` | `marketcolors.hollow` |
| `wicks.color` | Candlesticks | neutral wick (yahoo-style); defaults follow the edges | `marketcolors.wick.up/down` |
| `edge.up.color` / `edge.down.color` | Candlesticks | body outlines; default to `candle.up/down` colors | `marketcolors.edge.up/down` |
| `candle.alpha` | Candlesticks | `alpha` kwarg (`None` → setting, else 1.0) | `marketcolors.alpha` |
| `candle.hollow` | Candlesticks | `hollow` kwarg mirror (`None` → setting → resolved-face default) | — (their `type=` territory) |
| `candle.use_prev_close` | Candlesticks | `use_prev_close` kwarg mirror (`None` → setting, else False) | — (their `type='hollow_and_filled'` territory) |
| ~~`candle.width`~~ | Candlesticks | declined — width is data-density, not style | width subsystem (not style) |
| `ohlc.up.color` | OHLC | `colorup` kwarg (`None` → setting, else `text.color`) | `marketcolors.ohlc.up` |
| `ohlc.down.color` | OHLC | `colordn` kwarg (ditto) | `marketcolors.ohlc.down` |
| `ohlc.alpha` | OHLC | `alpha` kwarg (`None` → setting, else 1.0) | `marketcolors.alpha` |
| ~~`ohlc.width`~~ | OHLC | declined — width is data-density, not style (same verdict as `candle.width`) | width subsystem |
| `volume.up.color` | Volume | `colorup` kwarg (`None` → setting, else `~green`) | `marketcolors.volume.up` |
| `volume.down.color` | Volume | `colordn` kwarg (ditto, `~red`) | `marketcolors.volume.down` |
| `volume.ma.color` | Volume | `colorma` kwarg (ditto, `~gray`) | — (their mav is price-pane) |
| `volume.alpha` | Volume | `alpha` kwarg (`None` → setting, else 0.5; bars + ma line) | `marketcolors.volume_alpha` |
| ~~`volume.width`~~ | Volume | declined — width is data-density, not style | width subsystem |

## Indicator traces (AutoPlot and explicit plots)

| Key | Consumer | Notes |
|---|---|---|
| `<indicator>.color` | AutoPlot lines | any prefix role: `sma.color`, `ema.color`, `rsi.color`; list value = per-pane cycle (≈ mplfinance `mavcolors`) |
| `macd.color`, `macdsignal.color`, `macdhist.color` | AutoPlot multi-column | per-column roles via column names (old INI precedent); same pattern for `ppo`, `bbands` band color via indicator label |
| `lineplot.color` / `.alpha` / `.width` / `.linestyle` | LinePlot | kwargs exist today (≈ mplfinance `linecolor` for `type=line`) |
| `areaplot.color` / `.alpha` | AreaPlot | kwargs exist today |
| `barplot.color` / `.alpha` / `.width` | BarPlot | kwargs exist today |

## Condition / pattern / reference primitives

| Key | Consumer | Today's parameter / default |
|---|---|---|
| `stripes.color` / `stripes.alpha` | Stripes | `color`, `alpha` kwargs |
| `marker.color` / `marker.alpha` | Markers | `color`, `alpha` kwargs (old INI had `marker.entry`/`marker.exit` variants — revisit if entry/exit markers return) |
| `swings.color` | Swings | `color` kwarg |
| `zigzag.color` | ZigZag | hardcoded `color=None` today |
| `trendline.support.color` / `trendline.resistance.color` | TrendLines | `colors` tuple / `("green", "red")` |
| `hline.color` / `hline.linestyle` | HLine | `color`, `linestyle` / `grid.color` |
| `vline.color` / `vline.linestyle` | VLine | `color`, `linestyle` / `grid.color` |

## mplfinance coverage accounting

Every style-exposed mplfinance knob, and where it lands here:

| mplfinance | Disposition |
|---|---|
| `marketcolors.candle/ohlc/volume` up/down | ✓ `candle.*`, `ohlc.*`, `volume.*` above |
| `marketcolors.wick`, `marketcolors.edge` | ✓ `wicks.color` (flat) and `edge.up.color`/`edge.down.color` (per-direction); a per-direction wick split is representable later as `wicks.up.color` (grammar is positional-from-the-right) if a style ever needs it |
| `marketcolors.hollow` | ✓ `candle.off.color` |
| `marketcolors.alpha`, `volume_alpha` | ✓ `candle.alpha` / `ohlc.alpha`, `volume.alpha` |
| `mavcolors` | ✓ list-valued `sma.color` / `ema.color` |
| `linecolor` (plot kwarg) | ✓ `lineplot.color` |
| `marketcolors.vcedge` | ✗ declined — volume bar edges, no mplchart concept |
| `marketcolors.vcdopcod` | ✗ declined — behavior flag, not styling |
| `marketcolor_overrides` (per-bar array) | ✗ declined — data-driven coloring, primitive-kwarg territory if ever |
| `facecolor`, `figcolor`, `edgecolor`, `gridcolor`, `gridstyle`, `gridaxis` | rc layer (`axes.facecolor`, `grid.color`, …), not settings |
| `base_mpl_style`, `rc` | style spec sections, not settings |
| `y_on_right` | ✗ layout, Canvas territory (panes hardcode ticks-right); revisit only on demand |
| `figscale`, `fontscale`, width subsystem | rc / `figsize` / primitive kwargs, not style |

## Open questions

- Facet for line style: `linestyle` (matplotlib lingo, used here) vs LinePlot's current `style` kwarg — align at retrofit.
- Marker symbol as a facet (`marker.marker`? `marker.symbol`?) — awkward either way; may stay kwarg-only.
- `zigzag.color` requires adding a color parameter to ZigZag first.
- Whether AutoPlot band/hist coloring warrants dedicated facets (`<indicator>.band.alpha`?) or stays derived.
