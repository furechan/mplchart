"""mplchart utils"""

import pandas as pd

from types import MappingProxyType
from inspect import Signature, Parameter

TALIB_SAME_SCALE = "Output scale same as input"



def make_info(**kwargs):
    """make info mapping"""

    return MappingProxyType(kwargs)


def get_info(indicator, name: str, default=None):
    """get metadata from from `info` dict or attributes"""

    if hasattr(indicator, "info"):  # info dict
        info = indicator.info
        return info.get(name, default)
    
    return getattr(indicator, name, default)


def same_scale(indicator):
    """Whether indicator uses the same scale as inputs"""

    if hasattr(indicator, "function_flags"):  # talib
        flags = indicator.function_flags or ()
        return TALIB_SAME_SCALE in flags

    return get_info(indicator, "same_scale", False)


def get_name(indicator):
    """indicator name"""

    if hasattr(indicator, "func_object"):  # talib
        return indicator.info.get("name")

    if hasattr(indicator, "__name__"):  # function
        return indicator.name.removeprefix("calc_")

    return indicator.__class__.__name__


def get_label(indicator):
    """indicator label"""

    if hasattr(indicator, "func_object"):  # talib
        name = indicator.info.get("name")
        params = [repr(v) for v in indicator.parameters.values()]
        return name + "(" + ", ".join(params) + ")"

    return str(indicator)


def series_xy(data, item=None, *, dropna=False):
    """split data into x, y arrays"""

    if item is not None:
        data = data[item]

    if dropna:
        data = data.dropna()

    x = data.index.values
    y = data.values

    return x, y


def series_data(data, item: str = None, *, default_item: str = None, strict: bool = False):
    """extract series data depending on data type and parameters"""
    if isinstance(data, pd.DataFrame):
        if item is not None:
            return data[item]
        elif default_item is not None:
            return data[default_item]
        else:
            raise ValueError("Item is required for a DataFrame")

    if isinstance(data, pd.Series):
        if item is None or not strict:
            return data
        else:
            raise ValueError("Item must be None for a Series")

    raise TypeError(f"Invalid series type {type(data).__name__} !")



def get_series(prices, item: str = None):
    """extract column by name if applicable"""

    if isinstance(prices, pd.Series):
        if item is not None:
            raise ValueError(f"Expected dataframe with an {item!r} column")
        else:
            return prices

    if isinstance(prices, pd.DataFrame):
        # prices = prices.rename(columns=str.lower)
        item = item or "close"
        return prices[item]

    raise TypeError(f"Invalid series type {type(prices).__name__} !")



def short_repr(self):
    """short repr based on __init__ signature"""

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
