""" datetime utils """

import pandas as pd


def date_ticks(start, end, max_ticks=14):
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)

    step = (end - start) / max_ticks / pd.Timedelta(days=1)

    freq_list = ((1, "D"), (7, "W"), (14, "2W"), (30, "MS"), (90, "QS"), (360, "Y"))

    freq = next((f for s, f in freq_list if step <= s), "5Y")

    dates = pd.date_range(start=start, end=end, freq=freq)

    return dates


def date_labels(dates):
    labels = []
    year = month = None

    for date in dates:
        if date is None:
            labels.append("")
            continue
        prevy, prevm = year, month
        year, month = date.year, date.month
        fmt = []

        if prevy and year != prevy:
            fmt.append("%Y")

        elif prevm and month != prevm:
            fmt.append("%b")

        if not fmt or date.day >= 7:
            fmt.append("%d")

        fmt = "-".join(fmt)
        label = date.strftime(fmt)
        labels.append(label)

    return labels


# note week days start at sunday=0
def week_number(date, step=None, start=1):
    number = int((date.toordinal() - start) / 7)
    if step:
        number = number - (number - 1) % step
    return number


def month_number(date, step=None):
    number = date.year * 12 + date.month
    if step:
        number = number - (number - 1) % step
    return number


def year_number(date, step=None):
    number = date.year
    if step:
        number = number - number % step
    return number


def weekly_filter(step=None):
    last = new = None

    def filter_func(date):
        nonlocal last, new
        last, new = new, week_number(date, step=step)
        return new != last if last else date.weekday() <= 2

    return filter_func


def monthly_filter(step=None):
    last = new = None

    def filter_func(date):
        nonlocal last, new
        last, new = new, month_number(date, step=step)
        return new != last if last else date.day <= 7

    return filter_func


def yearly_filter(step=None):
    last = new = None

    def filter_func(date):
        nonlocal last, new
        last, new = new, year_number(date, step=step)
        return new != last if last else date.day <= 7

    return filter_func


def filter_dates(dates, max_ticks=10):
    start = dates[0]
    end = dates[-1]

    days = end.toordinal() - start.toordinal()
    interval = days / max_ticks

    if interval <= 1:
        date_filter = None
    elif interval <= 7:
        date_filter = weekly_filter()
    elif interval <= 30:
        date_filter = monthly_filter()
    elif interval <= 60:
        date_filter = monthly_filter(2)
    elif interval <= 90:
        date_filter = monthly_filter(3)
    elif interval <= 360:
        date_filter = yearly_filter()
    else:
        date_filter = yearly_filter(5)

    result = [d for d in dates if date_filter(date_filter(d))]

    return result
