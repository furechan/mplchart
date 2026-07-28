# Themes Review

Survey of the style/theme landscape available to mplchart charts, July 2026. Versions surveyed: matplotlib 3.10.8, morethemes 0.7.0, mplfinance 0.12.10b0.

## What resolves as a `style=` value

`Chart(style=...)` normalizes through `get_styler` in this order: mplchart shipped styles (`styles/lib/<name>.py`, which shadow), then matplotlib stylesheet names, then external theme providers (morethemes). mplfinance styles are **not** consumable — they are a different data structure (`marketcolors` dicts plus a `base_mpl_style`), surveyed here for comparison only.

Only mplchart's own styles carry chart-specific settings (`candle.*`, grid opinions). Matplotlib sheets and morethemes set rcParams only — they are the complete look, with no mplchart opinions layered on.

## mplchart shipped styles (4)

| Name | Description |
|---|---|
| `mplchart` | Default: factory template plus two grid opinions; mono hollow candles |
| `chartist` | Classic TA look — colored hollow candles keyed to *previous* close (StockCharts-style); mode flags live in-style |
| `modern` | Contemporary web-platform look — teal/red filled candles on white, light solid grid |
| `nightclouds` | Dark theme, mplfinance-inspired |

Descriptions above come from header comments in `styles/lib/*.py` — they are not machine-readable, so `available_styles()` returns bare names (see Follow-ups).

## morethemes (16)

Publication and editorial looks; each theme ships its own description string (`morethemes.themes.ALL_THEMES`).

| Name | Description |
|---|---|
| `wsj` | Refined newspaper style after the Wall Street Journal |
| `ft` | Muted palette, strong typographic character (Financial Times) |
| `economist` | Crisp, data-focused, subtle gridlines, sharp contrast |
| `yellowish` | Bold National Geographic-inspired warm yellow backdrop |
| `urban` | Clean and professional, Urbanist font, muted tones |
| `minimal` | Distraction-free monochrome |
| `nature` | Earthy tones, organic feel |
| `monoblue` | High-contrast shades of blue |
| `lighter` | Clean modern light theme for technical charts |
| `lumen` | Color-blind-friendly light |
| `ebonis` | Color-blind-friendly dark |
| `darker` | No-frills high-contrast dark |
| `greenwave` | Dark with vibrant green accents |
| `vscode-dark` | VS Code dark mode |
| `nord` | Arctic Nord palette, frosty blues |
| `retro` | Vintage / retro-gaming nostalgia |

## matplotlib built-ins (~28)

General-purpose sheets: `default`, `classic`, `fast`, `bmh`, `ggplot`, `fivethirtyeight`, `Solarize_Light2`, `dark_background`, `grayscale`, `petroff10`, `tableau-colorblind10`, plus ~17 `seaborn-v0_8-*` variants (`-darkgrid`, `-white`, `-whitegrid`, `-ticks`, `-paper`, `-notebook`, `-talk`, `-poster`, `-bright`, `-colorblind`, `-deep`, `-muted`, `-pastel`, `-dark`, `-dark-palette`). Colors, grid and typography only — no candle opinions.

## mplfinance (16) — comparison only

Each is a `base_mpl_style` plus market colors:

| Name | Base | Candles up/down |
|---|---|---|
| `yahoo` | fast | `#00b060` / `#fe3032` |
| `tradingview` | fast | `#26a69a` / `#ef5350` |
| `binance` | seaborn-darkgrid | `#70a800` / `#ea0070` |
| `binancedark` | dark_background | `#3dc985` / `#ef4f60` |
| `charles` | fast | `#006340` / `#a02128` |
| `ibd` | fast | `#2A3FE5` / `#DB39AD` |
| `sas` / `starsandstripes` | fast | `#082865` / `#ae0019` |
| `blueskies` | fast | white / `#0095ff` on `#dbf1ff` |
| `brasil` | fast | `#fedf00` / `#002776` |
| `checkers` | ggplot | black / red |
| `classic` | fast | white / black |
| `default` | seaborn-darkgrid | white / black on `#DCE3EF` |
| `kenan` | seaborn-darkgrid | black / red |
| `mike` | dark_background | black / `#0080ff` |
| `nightclouds` | dark_background | white / `#0095ff` on `#0b0b0b` |

`nightclouds` is the one already ported natively to mplchart.

## Follow-ups

- mplchart styles have no machine-readable description — a `DESCRIPTION` key in each `STYLE` dict would let `available_styles()` and the API reference show what each look is (currently header comments only).
- No docs page shows the looks side by side. The gallery shows chart *types*; a "styles and themes" tutorial rendering the four native styles plus matplotlib/morethemes usage is the visible gap. Needs executed chart cells per style — sizeable, and a candidate for the backlog rather than an inline edit.

Related: `notes/styler-settings.md`, `notes/styler-sketch.md`, memory `project-style-system`.
