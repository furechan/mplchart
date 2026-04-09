"""mplchart utils"""

import numpy as np

from inspect import Signature, Parameter


def detect_backend(df) -> str:
    """detect dataframe backend from module name"""
    return getattr(type(df), "__module__", "").partition(".")[0]


def is_polars(df) -> bool:
    """check if dataframe is polars"""
    return detect_backend(df) == "polars"


def is_pandas(df) -> bool:
    """check if dataframe is pandas"""
    return detect_backend(df) == "pandas"


def is_expr(item) -> bool:
    """check if item is a polars Expr (duck typing, no import)"""
    return hasattr(item, "meta")


def normalize_columns(df):
    """lowercase column names for both backends"""
    match detect_backend(df):
        case "polars":
            return df.rename({c: c.lower() for c in df.columns})
        case "pandas":
            return df.rename(columns=str.lower)
        case backend:
            raise ValueError(f"Unsupported backend {backend!r}")


def extract_datetime(df) -> np.ndarray:
    """extract datetime as tz-naive numpy array in local time"""
    match detect_backend(df):
        case "polars":
            return df["datetime"].dt.replace_time_zone(None).to_numpy()
        case "pandas":
            return df.index.tz_localize(None).values
        case backend:
            raise ValueError(f"Unsupported backend {backend!r}")


def col_to_numpy(df, col: str) -> np.ndarray:
    """extract a named column as numpy array for both backends"""
    return df[col].to_numpy()


def dataframe_eval(df, expr):
    """evaluate an expression against a DataFrame, returning a Series.

    Args:
        df: pandas or polars DataFrame
        expr: a polars Expr, or a string expression (e.g. ``"rsi < 30"``)
            - pandas: evaluated via ``df.eval(expr)``
            - polars: evaluated via ``df.sql("SELECT {expr} FROM self")``
    """
    if is_expr(expr):
        return df.select(expr).to_series()
    match detect_backend(df):
        case "pandas":
            return df.eval(expr)
        case "polars":
            return df.sql(f"SELECT {expr} FROM self").to_series()
        case backend:
            raise ValueError(f"Unsupported backend {backend!r}")


def get_metadata(indicator, name: str, default=None):
    """get metadata from `metadata` dict if present or attributes"""

    metadata = getattr(indicator, "metadata", None)
    if metadata is not None:
        return metadata.get(name, default)

    return getattr(indicator, name, default)


def same_scale(indicator):
    """Whether indicator uses the same scale as inputs"""

    TALIB_SAME_SCALE = "Output scale same as input"

    if hasattr(indicator, "function_flags"):  # talib
        flags = indicator.function_flags or ()
        return TALIB_SAME_SCALE in flags

    return get_metadata(indicator, "same_scale", False)


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


def series_xy(data, item: str | None = None, *, dropna: bool = False):
    """split data into x, y arrays"""

    if item is not None:
        data = data[item]

    if dropna:
        data = data.dropna()

    x = data.index.values
    y = data.values

    return x, y


# QUESTION Do we need both get_series and series_data methods
# They are the same except for the default_item paramater


def series_data(data, item=None, *, default_item: str | None = None):
    """extract series data depending on data type and parameters"""

    if is_expr(item):
        return data.select(item).to_series()

    if hasattr(data, "columns"):
        if item is not None:
            return data[item]
        elif default_item is not None:
            return data[default_item]
        else:
            raise ValueError("Item is required for a DataFrame")

    if item is not None:
        raise ValueError("Cannot specify item for non-DataFrame data.")
    else:
        return data


def get_series(prices, item=None):
    """extract column by name if applicable"""

    return series_data(prices, item, default_item="close")


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


def convert_dataframe(data, backend: str = "pandas"):
    """convert data to target format"""

    pname = getattr(data, '__module__', '').partition('.')[0]

    if backend == pname:
        return data

    if backend == "pandas":
        if hasattr(data, 'to_pandas'):
            return data.to_pandas()
        else:
            raise ValueError(f"Cannot convert {type(data)!r} to pandas")

    if backend == "polars":
        import polars

        if pname == 'pandas':
            return polars.from_pandas(data, include_index=True)
        else:
            return polars.from_dataframe(data)

    raise ValueError(f"Unknown backend {backend!r}")
