""" ticker formatters """

import matplotlib.ticker as mticker

from .datetime import date_labels


class DateIndexFormatter(mticker.Formatter):
    """Formatter based on a pandas DateTimeIndex"""

    def __init__(self, index, *, fmt="%Y-%m-%d"):
        if index is None:
            raise ValueError("index is None!")

        self.index = index
        self.fmt = fmt

    def __call__(self, value, pos=None):
        return self.format_data(value)

    def get_date(self, value):
        """date from index value"""

        idx = int(round(value))

        if idx < 0 or idx >= len(self.index):
            return None

        return self.index[idx]

    def format_data(self, value):
        """date label"""
        date = self.get_date(value)
        result = date.strftime(self.fmt) if date else None
        return result

    def format_ticks(self, values):
        """date labels"""
        dates = [self.get_date(v) for v in values]
        return date_labels(dates)
