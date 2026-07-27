# Styles Mismatch — mplfinance vs mplchart

How mplfinance style dicts map onto mplchart styles. Findings from a July 2026 experiment (mplfinance 0.12.10b0, matplotlib 3.10.8). Key inventory below is exhaustive — all 16 shipped mpf styles surveyed, with usage counts.

**Verified 2026-07-27, after closing the three gaps below:** a ~45-line converter maps all 16 styles with **zero unmapped keys**, all 16 render (candlesticks + SMA + volume, and OHLC + volume), and the rendered candle edges, wicks, volume faces and volume edges match the mplfinance spec **exactly** for every style. The two models are now equivalent for everything mpf styles express.

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
| `mavcolors` | `rc["axes.prop_cycle"]` (via cycler) |
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

## Gotcha

Three mpf styles (`binance`, `default`, `kenan`) declare `base_mpl_style: "seaborn-darkgrid"`, a stylesheet name matplotlib retired. Any converter needs to alias the legacy `seaborn-*` names to `seaborn-v0_8-*` — this was the only conversion failure before the alias was added.

Volume outlines cannot use `"none"` as a per-bar array entry: matplotlib parses it to transparent black, then the collection alpha overrides the alpha channel, producing visible semi-transparent outlines. Hence the pair rule (neither side set → no outline; one side set → the other follows its face).

## Status

No converter shipped — the validation harness lived in a scratchpad and was not kept. Its full mapping is the "Direct mappings" table above, so it can be rebuilt from this note in minutes; the pieces that took experimenting to find (the `seaborn-*` alias, the `"none"` edge trap, the exact role names) are recorded in Gotcha.

Options if it ever matters: port selected mpf palettes into `styles/lib/` as shipped styles, or expose a `from_mplfinance` utility so users bring their own. Neither is scheduled — and note the converter is only worth shipping if users actually have custom mpf styles to bring; the 16 built-ins would be better ported once as native palettes than converted at runtime.

Note for issue #19 (platform themes): converting mpf styles does **not** deliver ThinkOrSwim/Bloomberg/IBKR looks — those do not exist in mplfinance either (see `notes/themes-review.md`). Platform palettes have to be sampled from real screenshots.

Related: `notes/themes-review.md`, `notes/candlestick-styles.md`, `notes/style-settings.md`.
