# Styles Mismatch — mplfinance vs mplchart

How mplfinance style dicts map onto mplchart styles, and where the two models diverge. Findings from a July 2026 experiment (mplfinance 0.12.10b0, matplotlib 3.10.8): a ~30-line converter rendered 7 of 8 sampled mpf styles correctly on the first try.

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
| `marketcolors.alpha` | `settings["candle.alpha"]` |
| `y_on_right` | `rc["ytick.labelright"]` + `labelleft` / `right` / `left` |
| `style_name`, `base_mpf_style` | — (metadata, no equivalent needed) |

## The mismatch

**mpf has, mplchart does not:**

- ~~`marketcolors.wick.up` / `.down` — directional wick colors~~ — closed 2026-07-27: `wicks.up.color` / `wicks.down.color` added (each side falling back to its edge), replacing the flat `wicks.color`. `tradingview`'s teal/red wicks now convert exactly; neutral wicks are both sides set alike.
- `marketcolors.vcedge` — volume bar edge color. mplchart volume has no edge setting.
- `marketcolors.vcdopcod` — "volume color depends on price change, not candle direction" mode flag. mplchart always colors volume by bar direction.

**mplchart has, mpf does not** (the model is a superset on candles):

- `candle.hollow` and `candle.use_prev_close` mode flags — the `chartist` style ships them in-style; mpf treats hollow as a plot type, not a style property.
- `candle.off.color` — explicit hollow-body fill (mpf implies `facecolor`).
- Symbolic color values (`"~green"` snap-to-cycle, `"line"`/`"fill"` sentinels) and per-pane color cycling — no mpf equivalent.

## Gotcha

Three mpf styles (`binance`, `default`, `kenan`) declare `base_mpl_style: "seaborn-darkgrid"`, a stylesheet name matplotlib retired. Any converter needs to alias the legacy `seaborn-*` names to `seaborn-v0_8-*`. This was the single failure of the eight sampled.

## Status

No converter shipped — the experiment lived in a scratchpad. Options if it ever matters: port selected mpf palettes into `styles/lib/` as shipped styles, or expose a `from_mplfinance` utility so users bring their own. Neither is scheduled; recorded here so the analysis does not have to be redone.

Note for issue #19 (platform themes): converting mpf styles does **not** deliver ThinkOrSwim/Bloomberg/IBKR looks — those do not exist in mplfinance either (see `notes/themes-review.md`). Platform palettes have to be sampled from real screenshots.

Related: `notes/themes-review.md`, `notes/candlestick-styles.md`, `notes/style-settings.md`.
