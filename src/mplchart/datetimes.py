""" datetime utilities for mplchart """

import re
import logging

import numpy as np
import datetime as dt


logger = logging.getLogger(__name__)


"""
strftime formats specifiers
%Y  Year with century
%b  Month abbreviated name
%d  Day of the month zero-padded
%H  Hour (24-hour clock) zero-padded
%M  Minute zero-padded
%S  Second zero-padded
"""

"""
Numpy Date and Time Units
- Y: Year
- M: Month
- W: Week
- D: Day 
- h: Hour
- m: Minute
- s: Second
"""


FREQ_VALUES = {
    '1m': 1 / 1400,
    '2m': 2 / 1440,
    '5m': 5 / 1440,
    '10m': 10 / 1440,
    '20m': 20 / 1440,
    '30m': 30 / 1440,
    '1h': 1 / 24,
    '2h': 2 / 24,
    '1D': 1,
    '2D': 2,
    '1W': 7,
    '2W': 14,
    '1M': 30,
    '3M': 90,
    '1Y': 360,
    '2Y': 720,
    '5Y': 1800,
    '10Y': 3600
}


FREQ_VALUES = {
    'm': 1 / 1400,
    'h': 1 / 24,
    'D': 1,
    'W': 7,
    'M': 30,
    'Y': 360,
}


INTERVAL_STRETCH = 1.2


def round_up(value, levels=(1, 2, 5, 10, 15, 30)):
    """round a number to the nearest level"""

    levels = [x for x in levels if x >= value]
    level = min(levels) if levels else value // 1
    return level


def interval_freq(interval):
    interval = interval / np.timedelta64(1, 'D')
    interval = interval * INTERVAL_STRETCH

    for freq, value in reversed(FREQ_VALUES.items()):
        if interval >= value:
            return freq

    # default to seconds if no match found
    return '%ds' % (interval * 24 * 3600)


def date_ticks(dates, count=10):
    dates = np.asarray(dates, 'datetime64[s]')

    logger.debug("dates_ticks %r, %r, %r", dates[0], dates[-1], count)

    if count <= 0:
        return []

    if len(dates) <= count:
        return np.arange(len(dates))

    interval = (dates[-1] - dates[0]) / count
    freq = interval_freq(interval)

    if match := re.fullmatch(r'(\d+)([a-zA-Z]+)', freq):
        step = int(match.group(1))
        freq = match.group(2)
    else:
        step = 1

    logger.debug("dates_ticks %r, %r, %r", interval, freq, step)

    values = dates.astype(f"datetime64[{freq}]").astype(int)
    values = np.cumsum(np.r_[0, values[1:] != values[:-1]])

    step = round_up((values[-1] - values[0]) / count)

    values = values // step

    mask = np.concatenate(([False], values[1:] != values[:-1]))

    return np.where(mask)[0]




def date_labels(dates):
    """labels for a sequence of dates (numpy array of datetime)"""
    
    dates = np.asarray(dates, 'datetime64[s]').astype('O')

    count = len(dates)

    if count <= 1:
        return [d.strftime("%Y-%b-%d") for d in dates]
    
    #start, end = dates[0], dates[-1]
    #dayspan = (end - start) / dt.timedelta(days=1)
    #interval = dayspan / (count - 1)

    formats = {
        "%Y": "%Y",
        "%b-%d": "%b-%d",
        "%H:%M": "%H:%M",
        "%S": "%S",
    }

    labels = []
    pdate = dates[0] - (dates[1] - dates[0])

    for date in dates:
        for fmt in formats:
            label = date.strftime(fmt)
            prev = pdate.strftime(fmt)
            if label != prev:
                fmt = formats[fmt]
                label = date.strftime(fmt)
                break

        labels.append(label)
        pdate = date

    return labels

