# mplchart shipped style — pure data, zero imports (see notes/styler-sketch.md)
# chartist: the classic technical-analysis look — colored hollow candles by
# previous close (the StockCharts-style rendering); mode flags in-style
STYLE = {
    "rc": {
        "axes.grid": True,
        "grid.alpha": 0.4,
    },
    "settings": {
        "yaxis.right": True,
        "candle.up.color": "#0f9948",
        "candle.down.color": "#d91e18",
        "candle.hollow": True,
        "candle.use_prev_close": True,
        "ohlc.up.color": "#0f9948",
        "ohlc.down.color": "#d91e18",
        "volume.up.color": "#0f9948",
        "volume.down.color": "#d91e18",
    },
}
