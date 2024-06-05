""" ticker formatters """

import numpy as np
import pandas as pd

import matplotlib.ticker as mticker

"""
strftime formats specifiers
%Y  Year with century
%b  Month abbreviated name
%d  Day of the month zero-padded
%H  Hour (24-hour clock) zero-padded
%M  Minute zero-padded
%S  Second zero-padded
"""


def date_labels(dates):
    start, end, count = dates[0], dates[-1], len(dates)
    years = end.year - start.year
    months = years * 12 + end.month - start.month

    delta = (end - start) / pd.Timedelta(days=1)
    interval = delta / (count - 1) if count > 1 else 0

    if interval > 300:
        formats = ("%Y",)
    elif interval > 30:
        formats = ("%Y", "%b")
    elif interval > 0.5:
        formats = ("%Y", "%b", "%d") if months else ("%Y", "%b-%d")
    elif interval > 0:
        formats = ("%b-%d", "%H:%M")
    else:
        formats = ("%Y-%b-%d",)

    pdate = None
    labels = []

    for date in dates:
        label = None

        if pdate is None:
            fmt = formats[-1]
            label = date.strftime(fmt)
        else:
            for fmt in formats:
                label = date.strftime(fmt)
                prev = pdate.strftime(fmt)
                if label != prev:
                    break

        labels.append(label)
        pdate = date

    return labels


class DateIndexFormatter(mticker.Formatter):
    """Formatter based on a pandas DateTimeIndex"""

    def __init__(self, index, *, fmt="%Y-%m-%d"):
        if index is None:
            raise ValueError("index is None!")
        self.index = index
        self.fmt = fmt

    def __call__(self, value, pos=None):
        return self.format_data(value)

    def format_data(self, value):
        """date label"""
        size = len(self.index)
        idx = np.floor(value).astype(int).clip(0, size - 1)
        date = self.index[idx]
        result = date.strftime(self.fmt)
        return result

    def format_ticks(self, values):
        """date labels"""
        size = len(self.index)
        idx = np.floor(values).astype(int).clip(0, size - 1)
        dates = self.index[idx]
        return date_labels(dates)
