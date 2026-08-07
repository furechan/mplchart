""" datetime utilities for mplchart """

import re
import logging

import numpy as np

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
    'm': 1 / 1440,
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
    if hasattr(dates, "tz_localize"):
        dates = dates.tz_localize(None)

    dates = np.asarray(dates, 'datetime64[s]')

    logger.debug("dates_ticks %r, %r, %r", dates[0], dates[-1], count)

    if count <= 0:
        return []

    if len(dates) <= count:
        return np.arange(len(dates))

    interval = (dates[-1] - dates[0]) / count
    freq = interval_freq(interval)

    # strip any step prefix from the seconds fallback (e.g. "5400s" -> "s")
    if match := re.fullmatch(r'\d+([a-zA-Z]+)', freq):
        freq = match.group(1)

    logger.debug("dates_ticks %r, %r", interval, freq)

    values = dates.astype(f"datetime64[{freq}]").astype(int)
    values = np.cumsum(np.r_[0, values[1:] != values[:-1]])

    step = round_up((values[-1] - values[0]) / count)

    values = values // step

    mask = np.concatenate(([False], values[1:] != values[:-1]))

    return np.where(mask)[0]




def date_labels(dates):
    """labels for a sequence of dates (numpy array of datetime)"""
    
    if hasattr(dates, "tz_localize"):
        dates = dates.tz_localize(None)

    dates = np.asarray(dates, 'datetime64[s]').astype('O')

    count = len(dates)

    if count <= 1:
        return [d.strftime("%Y-%b-%d") for d in dates]
    
    formats = ("%Y", "%b-%d", "%H:%M", "%S")

    label = "*"
    labels = []
    pdate = dates[0] - (dates[1] - dates[0])

    for date in dates:
        for fmt in formats:
            label = date.strftime(fmt)
            prev = pdate.strftime(fmt)
            if label != prev:
                break

        labels.append(label)
        pdate = date

    return labels

