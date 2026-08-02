# the mplchart default style — pure data, zero imports
# (the whole default look: factory template + two grid opinions, right y labels,
# and a subtle volume bar rim;
# axes.grid / grid.alpha are the keys every style should be aware of)
STYLE = {
    "rc": {
        "axes.grid": True,
        "grid.alpha": 0.4,
    },
    "settings": {
        "yaxis.right": True,
        "volume.edge.lightness": 0.9,
    },
}
