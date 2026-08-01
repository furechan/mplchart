# mplchart shipped style — pure data, zero imports (see notes/styler-sketch.md)
# cascade: the moving-average look — every overlay draws the next color of a
# shared palette, the way mplfinance's mavcolors does. The aliases fold each
# moving-average prefix onto one "overlay" key, so a list-valued
# overlay.color cycles across indicators, not within one (see
# notes/styler-aliases.md). Everything else keeps the rc prop cycle.
STYLE = {
    "rc": {
        "axes.grid": True,
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "grid.color": "#dfe3ea",
        "grid.alpha": 1.0,
    },
    "aliases": {
        "sma": "overlay",
        "ema": "overlay",
        "wma": "overlay",
        "hma": "overlay",
        "rma": "overlay",
        "dema": "overlay",
        "tema": "overlay",
    },
    "settings": {
        "yaxis.right": True,
        "candle.up.color": "#2e7d32",
        "candle.down.color": "#c62828",
        "ohlc.up.color": "#2e7d32",
        "ohlc.down.color": "#c62828",
        "volume.up.color": "#2e7d32",
        "volume.down.color": "#c62828",
        "volume.alpha": 0.4,
        "overlay.color": ["#1565c0", "#ef6c00", "#6a1b9a", "#00838f"],
    },
}
