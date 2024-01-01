""" charting utils """


def series_xy(data, item=None, dropna=False):
    """split series into x, y arrays"""

    if item is not None:
        data = data[item]

    if dropna:
        data = data.dropna()

    x = data.index.values
    y = data.values

    return x, y
