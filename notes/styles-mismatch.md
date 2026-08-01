# Styles Mismatch — mplfinance vs mplchart

How mplfinance style dicts map onto mplchart styles. Findings from a July 2026 experiment (mplfinance 0.12.10b0, matplotlib 3.10.8). Key inventory below is exhaustive — all 16 shipped mpf styles surveyed, with usage counts.

**Verified 2026-07-27, after closing the three gaps below:** a ~45-line converter maps all 16 styles with **zero unmapped keys**, all 16 render (candlesticks + SMA + volume, and OHLC + volume), and the rendered candle edges, wicks, volume faces and volume edges match the mplfinance spec **exactly** for every style. Price-renderer colors are therefore equivalent; line colors are an approximation — see Cycles.

Every mpf style carries the same top-level keys (`base_mpl_style`, `marketcolors`, `mavcolors`, `y_on_right`, `gridcolor`, `gridstyle`, `facecolor`, `rc`) and the same `marketcolors` keys (`candle`, `edge`, `wick`, `ohlc`, `volume`, `vcedge`, `vcdopcod`, `alpha`) — plus two rare ones: `hollow` (1 style: `kenan`) and `volume_alpha` (1 style: `tradingview`).

## Why they map so well

mplfinance encodes chart colors in a nested `marketcolors` dict; mplchart encodes the same concepts as flat dotted settings keys (`candle.up.color`, `edge.down.color`, ...). Different shape, same vocabulary — so the conversion is mechanical.

## Direct mappings

| mplfinance | mplchart |
|---|---|
| `base_mpl_style` | `stylesheet` |
| `facecolor` | `rc["axes.facecolor"]` |
| `gridcolor` | `rc["grid.color"]` |
| `gridstyle` | `rc["grid.linestyle"]` |
| `rc` (list of pairs) | `rc` (dict) — just `dict(...)` |
| `mavcolors` | `rc["axes.prop_cycle"]` (via cycler) — **approximation, see Cycles below** |
| `marketcolors.candle.up` / `.down` | `settings["candle.up.color"]` / `["candle.down.color"]` |
| `marketcolors.edge.up` / `.down` | `settings["edge.up.color"]` / `["edge.down.color"]` |
| `marketcolors.wick.up` / `.down` | `settings["wicks.up.color"]` / `["wicks.down.color"]` |
| `marketcolors.ohlc.up` / `.down` | `settings["ohlc.up.color"]` / `["ohlc.down.color"]` |
| `marketcolors.volume.up` / `.down` | `settings["volume.up.color"]` / `["volume.down.color"]` |
| `marketcolors.vcdopcod` | `settings["volume.use_prev_close"]` (3 styles: `charles`, `ibd`, `yahoo`) |
| `marketcolors.vcedge` | `settings["volume.edge.up.color"]` / `["volume.edge.down.color"]`. Only `tradingview` sets it apart from the volume faces; for the same-as-faces case (the other 15) mpf does NOT draw same-color edges — its plotting substitutes the faces darkened to 90% HLS lightness (`_adjust_color_brightness`, found 2026-08-01 in `plotting.py`; the spec-level "edges match exactly" verification below missed this runtime substitution). The converter carries the intent as `settings["volume.edge.lightness"] = 0.90` — a Volume setting acting as a final transform on the effective edge colors (edges default to the faces first), implemented via `colors.scale_lightness`, which matches mpf's darkening math exactly |
| `marketcolors.hollow` | `settings["candle.off.color"]` (1 style: `kenan`) |
| `marketcolors.alpha` | `settings["candle.alpha"]` only — source-verified 2026-08-01: mpf applies it in the candlestick/hollow/renko collection constructors but never in `_construct_ohlc_collections`, so ohlc bars stay opaque (an earlier revision wrongly listed `ohlc.alpha` too) |
| `marketcolors.volume_alpha` | `settings["volume.alpha"]` (1 style: `tradingview`) |
| `y_on_right` | `settings["yaxis.right"]` (mapped 2026-08-01, once the `yaxis_right=` chart option landed; the earlier experiment mapped it as the four `ytick.labelright`/`labelleft`/`right`/`left` rc keys) — 11 of 16 styles put labels on the right |
| `style_name`, `base_mpf_style` | — (metadata, no equivalent needed) |

## The mismatch

**mpf has, mplchart does not** — all closed as of 2026-07-27; mplfinance's style model now maps in full:

- ~~`marketcolors.wick.up` / `.down` — directional wick colors~~ — closed 2026-07-27: `wicks.up.color` / `wicks.down.color` added (each side falling back to its edge), replacing the flat `wicks.color`. `tradingview`'s teal/red wicks now convert exactly; neutral wicks are both sides set alike.
- ~~`marketcolors.vcedge` — volume bar edge color~~ — closed 2026-07-27: `volume.edge.up.color` / `volume.edge.down.color` settings plus `edgeup=`/`edgedn=` kwargs. Outlines are opt-in as a pair: neither side set leaves bars unoutlined (the default look), one side set makes the other follow its face (the candle-edge rule — "none" inside a per-bar array would render as semi-transparent black once the collection alpha applies). Verified against `tradingview`'s white-on-teal/red.
- ~~`marketcolors.vcdopcod` — "volume color depends on price change, not candle direction" mode flag~~ — closed 2026-07-27: `volume.use_prev_close` (kwarg + setting, mirroring `candle.use_prev_close`; first bar compares to itself). The symmetry with candlesticks was the real argument; mpf parity for `charles`/`ibd`/`yahoo` came with it. Verified against `yahoo`'s colors.

**mplchart has, mpf does not** (the model is a superset on candles):

- `candle.hollow` and `candle.use_prev_close` mode flags — the `chartist` style ships them in-style; mpf treats hollow as a plot type, not a style property. (Note mpf *does* have `marketcolors.hollow`, but it is the hollow-body *fill color* — the twin of `candle.off.color`, not a mode flag.)
- Symbolic color values (`"~green"` snap-to-cycle, `"line"`/`"fill"` sentinels) and per-pane color cycling — no mpf equivalent.

## Cycles — the one real model difference

mplfinance runs **two parallel color cycles**:

1. `mavcolors` — a plain list turned into an `itertools.cycle` and consumed explicitly (`color=next(mavc)`) when drawing moving averages. It lives entirely outside rcParams.
2. the base stylesheet's `axes.prop_cycle`, which `plt.style.use(base_mpl_style)` leaves in place — it still drives addplots and anything else drawn on the axes.

So `mavcolors` does not override the stylesheet cycle; it bypasses it for MAs only. Survey of the 16 styles (2026-07-27): the mav palette is **never** equal to the sheet cycle (0/16) — 10 styles set a distinct palette, 6 set `mavcolors: None` and let MAs fall back to the rcParams cycle. Only 8 distinct mav palettes exist across the 16. They are short (2–7 colors vs matplotlib's 10) and purpose-built for overlaying a price pane, sometimes deliberately degenerate — `tradingview` is `['#2962ff', '#2962ff']` (all MAs the same blue), `mike` a near-black ramp.

mplchart has **one** cycle (the rcParams `axes.prop_cycle`) but consumes it *per role*: `resolve_color` keys a cycle per canonical role, so `SMA(20)`/`SMA(50)` take successive colors, and a role setting may itself be a list that cycles per role (`{"sma.color": [...]}`). That is more expressive per-indicator than mpf's single global MA cycle, but there is no "all moving averages" role to receive a mav palette wholesale.

Consequence for conversion: `mavcolors → rc["axes.prop_cycle"]` collapses mpf's two cycles into one. Note this is the **deliberate** mapping under the settled doctrine — [styler-settings.md](styler-settings.md) names `axes.prop_cycle` "the `mavcolors` generalization", with the tradeoff accepted explicitly ("a style that pins mav-ish cycle colors accepts that unclaimed pane indicators draw from the same palette — pin their roles to opt them out"). It is not a defect, and an earlier revision of this note wrongly framed it as a gap.

It is still a *fidelity* loss, and quantifying it is what this survey added: the mav palette never equals the sheet cycle (0 of 16), so the substitution always discards a cycle mpf would have kept. That evidence is one of the two grounds on which the doctrine was revised on 2026-07-27 in favour of **key aliases** — see [styler-aliases.md](styler-aliases.md). Under that design the conversion becomes `mavcolors` → list-valued `overlay.color` plus aliases `{"sma": "overlay", "ema": "overlay"}`, leaving `axes.prop_cycle` alone: two cycles on each side doing the same jobs. Key aliases shipped 2026-07-27, so a converter can now take that route; the converter itself remains exploratory (no conversion code in `src`).

## Gotcha

Three mpf styles (`binance`, `default`, `kenan`) declare `base_mpl_style: "seaborn-darkgrid"`, a stylesheet name matplotlib retired. Any converter needs to alias the legacy `seaborn-*` names to `seaborn-v0_8-*` — this was the only conversion failure before the alias was added.

Volume outlines cannot use `"none"` as a per-bar array entry: matplotlib parses it to transparent black, then the collection alpha overrides the alpha channel, producing visible semi-transparent outlines. Hence the pair rule (neither side set → no outline; one side set → the other follows its face).

## Status

**Converter shipped** (0.0.48): `styles/mplfinance.py` `load_mpf_style(name)` — name-only, str → Styler (the `make_mpf_style`-dict path existed briefly and was removed 2026-08-01) — with the `"mpf:"` style prefix as the string form (`Chart(style="mpf:yahoo")`, dispatched via the `mplchart.styles` entry-point group). It follows the mappings above in full — the last two special cases fell on 2026-08-01: `y_on_right` (initially excluded as chart layout) maps to `settings["yaxis.right"]` since the `yaxis_right=` chart option (param → `yaxis.right` setting → left) landed, and `vcedge` (initially skipped when equal to the volume faces as "invisible") always maps since the same-as-faces case was found to darken in mpf's rendering — see the table row. Renderer parity followed the same day: mpf bakes `marketcolors.alpha` into the candle *face* RGBA only (edges/wicks opaque — the implicit-rim twin of the vcedge darkening); mplchart's candlestick renderer originally applied alpha collection-wide and was changed to face-only to match. Volume alpha stays whole-artist on both sides (`ax.bar(..., alpha=)`). `mavcolors` take the key-alias route (shared `overlay.color` cycle), not the prop-cycle substitution. `marketcolors.alpha` maps to `candle.alpha` only (see the table row — the briefly-considered `ohlc.alpha` wire was a parity error, reverted same day).

Note for issue #19 (platform themes): converting mpf styles does **not** deliver ThinkOrSwim/Bloomberg/IBKR looks — those do not exist in mplfinance either (see `notes/themes-review.md`). Platform palettes have to be sampled from real screenshots.

Related: `notes/themes-review.md`, `notes/candlestick-styles.md`, `notes/styler-settings.md`.
