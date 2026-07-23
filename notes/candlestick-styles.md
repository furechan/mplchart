# Candlestick Styles — Scheme Taxonomy

Survey (2026-07-23) of single-mode candlestick coloring schemes across platforms, distilled from all 16 mplfinance shipped styles plus TradingView/StockCharts conventions. Grounds the `candle.*` settings in [style-settings.md](style-settings.md) and the six-color renderer surface in `plot_cspoly`. Companion to [styler-sketch.md](styler-sketch.md).

## The design space

Three elements × two directions — face (body fill), edge (body outline), wick — each up/dn. Six scalars cover every observed scheme; nothing surveyed needs per-bar or finer-than-element granularity. Every named scheme is a collapse of the six.

## The four scheme families

| Scheme | faceup | facedn | edgeup | edgedn | wickup | wickdn | Examples |
|---|---|---|---|---|---|---|---|
| **mono hollow** | background | X | X | X | X | X | mplchart default; mpf `classic`/`default` (white bg), `mike` (dark bg) |
| **two-color filled** | up | dn | up | dn | up | dn | mpf `tradingview`, `binance`, `charles`, `kenan`, +5 more |
| **yahoo-style** (filled + neutral wick) | up | dn | up | dn | neutral | neutral | mpf `yahoo`, `checkers` (gray), `nightclouds` (white on dark) |
| **colored hollow** (TV-hollow) | background | dn | up | dn | up | dn | mpf `blueskies`; TradingView "hollow candles" |

- "background" = `axes.facecolor`, not literal white — `mike` (dark style) proves hollow means face-matches-background.
- Notably absent across all 16 mpf styles: per-direction wicks differing from the edges; any style with face/edge/wick all three mutually distinct per direction. mplfinance's full `wick.up/down` generality is unused even by its own styles — supporting the flat `wicks.color` key.
- Cosmetic axis: `alpha` 0.9 vs 1.0, roughly half the mpf styles each.

## Renderer surface

`plot_cspoly(..., faceup, facedn, edgeup, edgedn, wickup, wickdn, faceoff=None, use_prev_close=False)` — final colors only, no styling policy. Bodies are 4-vertex rectangles (`PolyCollection` fast path); wicks are a separate `LineCollection`, two segments per bar (top → high, bottom → low), drawn beneath the bodies. Two segments (not one low→high line) so hollow bodies stay clean at `alpha < 1`. The split exists precisely because yahoo-style neutral wicks are inexpressible when body+wick share one polygon path.

Both criteria live here: the fill flag is always intrabar (`body_up = close >= open`); the up/dn color flag follows `use_prev_close`. ``faceoff`` is the third face color (≡ mplfinance `marketcolors.hollow`): the body fill for intrabar-up bodies — face selection is `where(body_up, faceoff, where(up, faceup, facedn))`; `None` = always filled. All four cells of the 2×2 are renderable, including StockCharts (`faceoff=` + `use_prev_close=True`).

Naming per layer (deliberate): the renderer speaks geometry — `faceup`/`facedn`/`faceoff` (mechanism-speak is correct at the mechanism layer); the settings speak domain — `candle.hollow.color` (palette) and `candle.scheme: "hollow" | "filled"` (the "use hollow candles" flag). Resolution: `scheme: hollow` → `faceoff = candle.hollow.color or background`; `scheme: filled` → `faceoff = None`.

## Primitive interface (adopted 2026-07-23)

Kwargs declare a complete scheme; **schemes are atomic — they never merge with the stylesheet**. Settings are consulted only when no scheme kwarg is given; rcParams (`text.color`, `axes.facecolor`) are the base defaults in both paths, so kwarg schemes stay theme-appropriate once the rc wiring lands.

```python
Candlesticks()                            # style drives (settings hook pending)
Candlesticks(color="navy")                # mono hollow in navy
Candlesticks(colorup="g", colordn="r")    # filled bicolor
Candlesticks(colorup="g", colordn="r", hollow=True)   # colored hollow (TV hollow candles)
Candlesticks(color=..., colorup=...)      # ValueError — competing schemes
Candlesticks(color="navy", hollow=False)  # ValueError at plot time — mono filled is direction-blind
Candlesticks(hollow=False)                # renders — default mode is never validated (may look weird)
```

Three color params plus the `hollow` mode flag (adopted 2026-07-23, reopening an earlier drop). The model: a scheme has two direction channels — color (up/dn palette) and fill (hollow-up) — and every readable scheme uses at least one. `hollow` is tri-state: `None` resolves per palette family (mono → `True`, fill being mono's only direction channel; bicolor → `False`, the filled convention), explicit `True` flips bicolor to colored hollow, and `False` with a mono palette raises (direction-blind; no surveyed style). The earlier prototype's standalone-mono-declaration reading stays dropped — `hollow` is mode, not palette, so schemes remain atomic. The yahoo-style neutral wick stays style-only. Consistency checks are params-only (settled 2026-07-23): params express intent, and settings/defaults bend to the params, never the reverse. Competing schemes raise at construction; an explicit mono `color=` combined with `hollow=False` or `use_prev_close` raises at plot time. The default mode (no color kwargs) is never validated against the style — bare flags apply as-is and the chart renders, possibly direction-blind. When `candle.scheme` lands, `hollow=None` additionally defers to it before the family default.

Scheme → six colors:

```python
if colorup or colordn:       # filled bicolor (missing side falls to textcolor)
    edgeup = wickup = faceup = colorup
    edgedn = wickdn = facedn = colordn
    faceoff = background if hollow else None
elif color:                  # mono hollow
    edgeup = edgedn = wickup = wickdn = facedn = color; faceup = background
else:                        # no color kwargs: settings (pending) → rcParams defaults
    edgeup = edgedn = wickup = wickdn = facedn = textcolor; faceup = background
```

## Settings path (implemented 2026-07-23)

For the no-kwargs path, four semantic keys expand to the six renderer colors plus `faceoff` (the settings-layer twin of the kwarg shuffle), resolved via `chart.canvas.resolve_color`:

| renderer | derivation |
|---|---|
| `faceup` / `facedn` | `candle.up.color` / `candle.down.color` (else textcolor) |
| `edgeup` / `edgedn` | `edge.up.color` / `edge.down.color` if set, else follow the faces |
| `wickup` / `wickdn` | `wicks.color` if set (neutral, yahoo-style), else follow the edges |
| `faceoff` | hollow mode only: `candle.hollow.color` (else background) |

Mode: the `hollow` kwarg if given, else the family default read off the resolved faces — `faceup == facedn` means mono (→ hollow), distinct faces mean bicolor (→ filled). No settings probe needed: mono-ness is a property of the resolved palette, whatever its source; `edge.*`/`wicks` never enter the comparison. `candle.hollow.color` presence does NOT flip the scheme, per the constraint below — it only picks the hollow-body fill. The explicit `candle.scheme` key is still future (lands with the Style spec). Mode kwargs compose with settings palettes — `hollow=True`/`use_prev_close=True` over `candle.up`/`candle.down` settings work like their kwarg-palette counterparts (this is how the StockCharts look ships style-side today).

Atomicity in the implementation: kwargs sanitize up front to two side colors — mono sets both sides to `color`, bicolor fills the missing side with textcolor, no kwargs leaves both unset — so `colorup is None ⇔ settings path`. Resolution is then one flat flow, one `resolve_color` call per renderer slot with the sanitized side as `override=`: under a kwarg scheme every slot is pinned (settings can never merge in) while kwarg colors still get the resolution pipeline (hex munging, `~` snapping). The `hollow` default reads off the resolved faces after resolution (`faceup == facedn` → hollow); consistency checks never look at the resolution — they are params-only, in the kwarg branches. `candle.alpha` (implemented 2026-07-23) is the one non-color facet: the `alpha` kwarg defaults to `None` and resolves the setting via `canvas.get_setting` (else 1.0) — explicit kwarg wins, same params-bend rule. The candlesticks module docstring carries the full settings quick-reference. Filled styles set only `up`/`down`; hollow styles additionally set `hollow` (they know their background from their own rc). All four scheme families are expressible in two to four keys; per-direction wick precision (`wicks.up.color`) stays a named-but-unimplemented escape hatch — no surveyed style needs it.

Naming: the hollow-fill key is `candle.hollow.color` — matches mplfinance's `marketcolors.hollow` and the scheme vocabulary; the `off` spelling was rejected as mechanism-speak *for the settings key* — it lives on at the renderer as `faceoff`, where mechanism-speak belongs.

## Emulation check (2026-07-23)

`playground/candlesticks-styles.ipynb` translates all 16 shipped mplfinance styles (`marketcolors` → settings via a prototype of the compat stretch goal; rc half via scoped `mpl.rc_context`, the manual stand-in for the pending rc wiring) — every candle look reproduces with the current settings surface, nothing missing. Caveat for the translator: styledata often spells inherit as concrete colors instead of `"i"`, so the wick check needs canonical color comparison (`normalize_color`) against the edges before declaring a key needed.

## Criteria — the 2×2 model

Two criteria exist: **intrabar** (close vs open) and **interbar** (close vs previous close). The fill flag (hollow/filled) is *always* intrabar — that is the definition of a candle body, no platform varies it. The color flag is the one genuine choice, and it exists in the basic schemes too:

| | color by intrabar | color by interbar |
|---|---|---|
| **filled** | TV default | pre-2026-07 mplchart look |
| **hollow** | TV hollow candles | **StockCharts** |

StockCharts' "two-mode" scheme is not a third mode — it is colored hollow × interbar. mplfinance implements it as `type='hollow_and_filled'` (edge/wick by prev-close via `use_prev_close=True`, body hollow by open/close, hollow bodies filled with `marketcolors.hollow`, default transparent).

Kwarg: `Candlesticks(colorup=, colordn=, use_prev_close=True)` selects interbar coloring (with an explicit mono `color=` the criterion is moot — plot-time ValueError; bare `use_prev_close` renders over whatever the style provides). First bar counts as up (compares to itself). Adding `hollow=True` reaches the hollow row — the StockCharts cell is `Candlesticks(colorup=, colordn=, hollow=True, use_prev_close=True)`, or the same mode kwargs over a `candle.up`/`candle.down` settings palette. A settings equivalent of the criterion itself (`candle.colorby`) could land with `candle.scheme`.

mplfinance's seven candle color slots (candle/edge/wick × up/down + hollow) never contradict because scheme selection lives outside the style (`type=`); no single renderer reads all seven. Our equivalent: an explicit `candle.scheme` mode key, so color keys are pure palette — `candle.hollow.color` presence must NOT flip the scheme (a complete palette would misrender).

## Out of scope (for now)

- Per-direction wick colors (`wicks.up.color`) — representable later, the grammar is positional-from-the-right; no surveyed style needs it.
- Per-bar color arrays (mpf `marketcolor_overrides`) — data-driven coloring, not styling.
