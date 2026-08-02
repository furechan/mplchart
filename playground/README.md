# Playground

Scratch and exploration notebooks — not user-facing documentation. For curated examples see [examples/](../examples/) and the published docs site.

## Core mechanics

- [manual-plot.ipynb](manual-plot.ipynb) — building a financial plot with raw matplotlib and the `dateaxis` machinery, without `Chart`
- [data-view.ipynb](data-view.ipynb) — `PandasDataView` slicing and windowing behavior
- [date-index.ipynb](date-index.ipynb) — pandas `DatetimeIndex` behavior exploration
- [sample-prices.ipynb](sample-prices.ipynb) — the bundled `sample_prices` dataset and its frequencies
- [heikin-ashi.ipynb](heikin-ashi.ipynb) — the `HeikinAshi` primitive and its `calc_heikin_ashi` indicator
- [swings-primitive.ipynb](swings-primitive.ipynb) — the `Swings` primitive: peaks and valleys on a bound indicator
- [mplchart-interact.ipynb](mplchart-interact.ipynb) — interactive charting with ipywidgets

## [styles/](styles/)

- [mplchart-styles.ipynb](styles/mplchart-styles.ipynb) — full charts under every shipped style, a stock matplotlib stylesheet, and a custom style dict
- [matplotlib-styles.ipynb](styles/matplotlib-styles.ipynb) — using matplotlib stylesheets with mplchart
- [mplfinance-styles.ipynb](styles/mplfinance-styles.ipynb) — `mpf:` prefix styles from mplfinance
- [morethemes-styles.ipynb](styles/morethemes-styles.ipynb) — `mt:` prefix themes from morethemes
- [grid-styles.ipynb](styles/grid-styles.ipynb) — grid styling under total styles
- [candlesticks-params.ipynb](styles/candlesticks-params.ipynb) — `Candlesticks` color kwargs walkthrough
- [candlesticks-styles.ipynb](styles/candlesticks-styles.ipynb) — `Candlesticks` settings path, including the mplfinance `marketcolors` translation
- [ohlc-styles.ipynb](styles/ohlc-styles.ipynb) — `OHLC` settings hook
- [volume-styles.ipynb](styles/volume-styles.ipynb) — `Volume` settings hook
- [styler-aliases.ipynb](styles/styler-aliases.ipynb) — key aliases renaming the settings lookup prefix
- [styles-playground.ipynb](styles/styles-playground.ipynb) — experiments with a hand-built `Styler`
- [yaxis-side.ipynb](styles/yaxis-side.ipynb) — `Chart(yaxis_right=)` and the `yaxis.right` style setting

## [integrations/](integrations/)

- [mintalib-indicators.ipynb](integrations/mintalib-indicators.ipynb) — mintalib indicators on the pandas backend
- [mintalib-expressions.ipynb](integrations/mintalib-expressions.ipynb) — mintalib polars expressions on the polars backend
- [talib-playground.ipynb](integrations/talib-playground.ipynb) — TA-Lib functions with mplchart
- [pandas-expressions.ipynb](integrations/pandas-expressions.ipynb) — pandas 3.0 `pd.col()` column expressions (experimental)
- [yfinance-prices.ipynb](integrations/yfinance-prices.ipynb) — fetching prices with yfinance

## [matplotlib/](matplotlib/)

Matplotlib behavior reference notebooks.

- [matplotlib-colors.ipynb](matplotlib/matplotlib-colors.ipynb) — named colors and colormaps
- [matplotlib-cycler.ipynb](matplotlib/matplotlib-cycler.ipynb) — property cyclers
- [matplotlib-rcparams.ipynb](matplotlib/matplotlib-rcparams.ipynb) — rcParams exploration
- [matplotlib-xticks.ipynb](matplotlib/matplotlib-xticks.ipynb) — tick locator and formatter behavior
- [matplotlib-autoscale.ipynb](matplotlib/matplotlib-autoscale.ipynb) — lines vs autoscale: out-of-range endpoints, data limits, `add_artist` clipping, `axline` anchors

## [prototypes/](prototypes/)

Frozen historical artifacts — self-contained notebooks that derived features now shipped in `src`, or preserve code removed from it. Kept as-is, not maintained.

- [renko-proto.ipynb](prototypes/renko-proto.ipynb) — Renko transform-then-render prototype (shipped as `Renko`)
- [pnf-proto.ipynb](prototypes/pnf-proto.ipynb) — Point & Figure prototype (shipped as `PointFigure`)
- [trend-lines-proto.ipynb](prototypes/trend-lines-proto.ipynb) — walkback trend-line detection (shipped as `TrendLines`, experimental)
- [candlesticks-as-bars.ipynb](prototypes/candlesticks-as-bars.ipynb) — preserved legacy `plot_csbars` renderer (candles as two `ax.bar` calls)

## [apps/](apps/)

Runnable scripts.

- [chart-from-script.py](apps/chart-from-script.py) — creating a chart from a plain script
- [streamlit-demo.py](apps/streamlit-demo.py) — mplchart in a Streamlit app
- [nicegui-demo.py](apps/nicegui-demo.py) — mplchart in a NiceGUI app
