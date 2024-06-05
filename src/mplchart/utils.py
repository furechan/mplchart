""" mplchart utils """


def get_label(indicator):
    """ label for indicator """
    label = getattr(indicator, "__name__", str(indicator))
    return label


def series_xy(data, item=None, dropna=False):
    """split series into x, y arrays"""

    if item is not None:
        data = data[item]

    if dropna:
        data = data.dropna()

    x = data.index.values
    y = data.values

    return x, y
