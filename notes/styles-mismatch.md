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
| `marketcolors.vcedge` | `settings["volume.edge.up.color"]` / `["volume.edge.down.color"]` (only `tradingview` sets it apart from the volume colors) |
| `marketcolors.hollow` | `settings["candle.off.color"]` (1 style: `kenan`) |
| `marketcolors.alpha` | `settings["candle.alpha"]` and `settings["ohlc.alpha"]` |
| `marketcolors.volume_alpha` | `settings["volume.alpha"]` (1 style: `tradingview`) |
| `y_on_right` | `rc["ytick.labelright"]` + `labelleft` / `right` / `left` — used by 11 of 16 styles; verified to render correctly |
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

Consequence for conversion: `mavcolors → rc["axes.prop_cycle"]` is an **approximation**, not an equivalence. It gives the intended look (mplchart indicator lines are the analog of mpf's MAs) but replaces the stylesheet's own cycle, which mpf would have kept for non-MA artists. Since no mav palette equals its sheet cycle, this substitution always changes something. A closer mapping would need either a "line/indicator default" role in mplchart or per-role palettes assigned at conversion time.

## Gotcha

Three mpf styles (`binance`, `default`, `kenan`) declare `base_mpl_style: "seaborn-darkgrid"`, a stylesheet name matplotlib retired. Any converter needs to alias the legacy `seaborn-*` names to `seaborn-v0_8-*` — this was the only conversion failure before the alias was added.

Volume outlines cannot use `"none"` as a per-bar array entry: matplotlib parses it to transparent black, then the collection alpha overrides the alpha channel, producing visible semi-transparent outlines. Hence the pair rule (neither side set → no outline; one side set → the other follows its face).

## Status

No converter shipped — the validation harness lived in a scratchpad and was not kept. Its full mapping is the "Direct mappings" table above, so it can be rebuilt from this note in minutes; the pieces that took experimenting to find (the `seaborn-*` alias, the `"none"` edge trap, the exact role names) are recorded in Gotcha.

Options if it ever matters: port selected mpf palettes into `styles/lib/` as shipped styles, or expose a `from_mplfinance` utility so users bring their own. Neither is scheduled — and note the converter is only worth shipping if users actually have custom mpf styles to bring; the 16 built-ins would be better ported once as native palettes than converted at runtime.

Note for issue #19 (platform themes): converting mpf styles does **not** deliver ThinkOrSwim/Bloomberg/IBKR looks — those do not exist in mplfinance either (see `notes/themes-review.md`). Platform palettes have to be sampled from real screenshots.

Related: `notes/themes-review.md`, `notes/candlestick-styles.md`, `notes/style-settings.md`.
