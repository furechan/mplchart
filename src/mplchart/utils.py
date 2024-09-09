""" mplchart utils """

import pandas as pd

from inspect import Signature, Parameter


def series_xy(data, item=None, dropna=False):
    """split series into x, y arrays"""

    if item is not None:
        data = data[item]

    if dropna:
        data = data.dropna()

    x = data.index.values
    y = data.values

    return x, y


def get_series(prices, item: str = None):
    """extract column by name if applicable"""

    if isinstance(prices, pd.Series):
        if item is not None:
            raise ValueError(f"Expected dataframe with an {item!r} column")
        else:
            return prices

    # rename columns to make lookup case insensitive
    prices = prices.rename(columns=str.lower)

    if item is not None:
        return prices[item.lower()]

    if isinstance(prices, pd.DataFrame):
        return prices["close"]


def short_repr(self):
    """ short repr based on __init__ signature """

    cname = self.__class__.__qualname__
    signature = Signature.from_callable(self.__init__)
    args, keyword_only = [], False

    for p in signature.parameters.values():
        v = getattr(self, p.name, p.default)

        if p.kind in (Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD):
            raise ValueError(f"Unsupported parameter type {p.kind}")

        if p.kind == Parameter.KEYWORD_ONLY:
            keyword_only = True
        elif isinstance(p.default, (type(None), str, bool)):
            keyword_only = True

        if v == p.default:
            # skip argument if not equal to default
            if keyword_only or not isinstance(v, (int, float)):
                keyword_only = True
                continue

        if keyword_only:
            args.append(f"{p.name}={v!r}")
        else:
            args.append(f"{v!r}")

    args = ", ".join(args)

    return f"{cname}({args})"
