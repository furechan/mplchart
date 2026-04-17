"""mplchart utils"""

import numpy as np

from inspect import Signature, Parameter


def calc_price(prices, item):
    """Get or compute a named price item from an OHLCV frame. Backend-agnostic."""
    if item in prices:
        return prices[item]

    if item in ("mid", "hl", "hl2"):
        return (prices["high"] + prices["low"]) / 2

    if item in ("typ", "hlc", "hlc3"):
        return (prices["high"] + prices["low"] + prices["close"]) / 3

    if item in ("wcl", "hlcc", "hlcc4"):
        return (prices["high"] + prices["low"] + prices["close"] * 2) / 4

    if item in ("avg", "ohlc", "ohlc4"):
        return (prices["open"] + prices["high"] + prices["low"] + prices["close"]) / 4

    raise ValueError(f"Invalid price item {item!r}")


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


def normalize_prices(prices):
    """Normalize a prices DataFrame for use with indicators and charting.

    Lowercases column names and, for pandas DataFrames, promotes a ``date``
    or ``datetime`` column to the index if present.
    """
    match detect_backend(prices):
        case "polars":
            return prices.rename({c: c.lower() for c in prices.columns})
        case "pandas":
            prices = prices.rename(columns=str.lower)
            if "datetime" in prices.columns:
                prices = prices.set_index("datetime")
            elif "date" in prices.columns:
                prices = prices.set_index("date")
            else:
                prices = prices.rename_axis(index=str.lower)
            return prices
        case backend:
            raise ValueError(f"Unsupported backend {backend!r}")


def check_prices(prices):
    """Raise ValueError if prices columns have not been normalized.

    Use :func:`normalize_prices` to prepare a prices DataFrame before
    passing it to indicators or the chart.
    """
    cols = list(prices.columns)
    if any(c != c.lower() for c in cols):
        raise ValueError(
            "prices columns must be lowercase — call normalize_prices(prices) first"
        )
    match detect_backend(prices):
        case "pandas":
            if "date" in cols or "datetime" in cols:
                raise ValueError(
                    "prices 'date'/'datetime' must be the index, not a column"
                    " — call normalize_prices(prices) first"
                )


def extract_datetime(df) -> np.ndarray:
    """extract datetime as tz-naive numpy array in local time"""
    match detect_backend(df):
        case "polars":
            import polars as pl
            col = next(
                (df[name] for name, dtype in df.schema.items()
                 if dtype == pl.Date or dtype == pl.Datetime),
                None,
            )
            if col is None:
                raise ValueError("No Date or Datetime column found in DataFrame")
            if col.dtype == pl.Date:
                return col.to_numpy()
            return col.dt.replace_time_zone(None).to_numpy()
        case "pandas":
            return df.index.tz_localize(None).values
        case backend:
            raise ValueError(f"Unsupported backend {backend!r}")


def col_to_numpy(df, col: str) -> np.ndarray:
    """extract a named column as numpy array for both backends"""
    return df[col].to_numpy()


def resolve_expr(df, expr):
    """resolve an expression against a DataFrame or Series, returning a Series.

    Args:
        df: pandas or polars DataFrame or Series
        expr: a polars Expr, or a string expression (e.g. ``"rsi < 30"``)
            - pandas: evaluated via ``df.eval(expr)``
            - polars: evaluated via ``df.sql("SELECT {expr} FROM self")``

    If ``df`` is a Series it is promoted to a single-column DataFrame using
    the series name as the column name, so string expressions can reference it.
    """
    if is_expr(expr):
        return df.select(expr).to_series()

    if callable(expr):
        return expr(df)

    # promote Series to single-column DataFrame so eval can reference by name
    match detect_backend(df):
        case "pandas":
            import pandas as pd
            if isinstance(df, pd.Series):
                df = df.to_frame()
            return df.eval(expr)
        case "polars":
            import polars as pl
            if isinstance(df, pl.Series):
                df = df.to_frame()
            return df.sql(f"SELECT {expr} FROM self").to_series()
        case backend:
            raise ValueError(f"Unsupported backend {backend!r}")


def get_metadata(indicator, name: str, default=None):
    """get metadata from `metadata` dict if present or attributes"""

    metadata = getattr(indicator, "metadata", None)
    if metadata is not None:
        return metadata.get(name, default)

    return getattr(indicator, name, default)



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

    if is_expr(indicator):
        try:
            return indicator.meta.output_name()
        except Exception:
            pass

    expr = getattr(indicator, "expr", None)
    if is_expr(expr):
        try:
            return expr.meta.output_name()
        except Exception:
            pass

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
