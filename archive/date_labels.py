""" ticker formatters """

import pandas as pd


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
    """labels for a sequence of dates (pandas based)"""
    
    start, end, count = dates[0], dates[-1], len(dates)
    years = end.year - start.year
    months = years * 12 + end.month - start.month
    days = (end - start) / pd.Timedelta(days=1)
    interval = days / (count - 1) if count > 1 else 0

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

