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


def is_polars_expr(item) -> bool:
    """check if item is a polars Expr"""
    return type(item).__module__ == "polars.expr.expr"


def is_polars_expr_like(item) -> bool:
    """True if item is a polars Expr or a tuple of polars Expr."""
    if is_polars_expr(item):
        return True
    if isinstance(item, tuple) and item and all(is_polars_expr(e) for e in item):
        return True
    return False


def is_pandas_expr(item) -> bool:
    """check if item is a pandas Expression"""
    return type(item).__module__ == "pandas.api.typing"


def is_indicator_like(item) -> bool:
    """True if item is any acceptable indicator form: column name, polars expr, tuple-of-Expr, pandas expr, or callable."""
    return isinstance(item, str) or is_polars_expr_like(item) or is_pandas_expr(item) or callable(item)


def apply_indicator(prices, indicator):
    """Apply an indicator or expression to prices.

    - str: column name — plain native column access (``prices[name]``);
      derived prices are indicators (e.g. ``TYPPRICE()``), not string aliases.
    - Polars Expr: evaluates against ``prices`` and returns a Series. If the
      Series is Struct-typed (e.g. ``pl.struct(MACD())``), it is unnested
      into a multi-column DataFrame.
    - Tuple of ``pl.Expr``: evaluates each and returns a DataFrame. Accepted
      for interop with libraries that emit tuple-of-Expr (e.g. mintalib);
      mplchart's own multi-output expressions return a struct Expr instead.
    - Pandas Expression: evaluates via ``_eval_expression`` and returns a Series.
    - Callable: returns ``indicator(prices)``.
    """
    if isinstance(indicator, str):
        return prices[indicator]

    if is_polars_expr(indicator):
        import polars as pl
        series = prices.select(indicator).to_series()
        if isinstance(series.dtype, pl.Struct):
            return series.struct.unnest()
        return series

    if isinstance(indicator, tuple) and indicator and all(is_polars_expr(e) for e in indicator):
        import polars as pl
        series = [prices.select(e).to_series() for e in indicator]
        return pl.DataFrame({s.name: s for s in series})

    if is_pandas_expr(indicator):
        return indicator._eval_expression(prices)

    if callable(indicator):
        return indicator(prices)

    raise TypeError(
        f"Cannot apply {type(indicator).__name__!r} to prices: "
        f"expected a column name, polars Expr, tuple of Expr, pandas Expression, or callable indicator."
    )



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
            "prices columns must be lowercase — pass normalize=True or call normalize_prices(prices)"
        )

    match detect_backend(prices):
        case "pandas":
            if "date" in cols or "datetime" in cols:
                raise ValueError(
                    "prices 'date'/'datetime' must be the index, not a column"
                )


def col_to_numpy(df, col: str) -> np.ndarray:
    """extract a named column as numpy array for both backends"""
    return df[col].to_numpy()


def get_metadata(indicator, name: str, default=None):
    """get named attribute from indicator, with a default"""

    if is_pandas_expr(indicator):
        return default

    return getattr(indicator, name, default)



def extract_prefix(text: str) -> str:
    """Extract a normalized short prefix from an identifier-ish string.

    Splits on the first ``(``, ``-``, or whitespace and lowercases the result.
    Examples: ``"macd-12-26-9"`` → ``"macd"``, ``"MACD(12, 26, 9)"`` → ``"macd"``,
    ``"sma(20)"`` → ``"sma"``.
    """
    import re
    match = re.match(r"[^-(\s]+", text)
    return match.group(0).lower() if match else text.lower()


def get_label(indicator):
    """Human-readable legend text for an indicator or expression.

    Resolution order:
    1. pandas ``Expression`` → ``repr(indicator)`` (must come first, see below)
    2. explicit ``.label`` attribute (set by custom wrappers)
    3. talib ``func_object`` → ``"name(params)"``
    4. polars ``Expr`` → ``.meta.output_name()``
    5. fall back to ``repr(indicator)``

    The color map uses the label's prefix via :func:`extract_prefix` when no
    direct match is found in ``color_scheme``.
    """

    if isinstance(indicator, str):
        return indicator

    # This check MUST stay first among attribute-based checks:
    # Expression.__getattr__ hijacks any attribute
    # access (hasattr is always True, getattr never falls back), so the
    # instance-level getattr/hasattr checks below are only safe once
    # expressions have returned early.
    if is_pandas_expr(indicator):
        return repr(indicator)

    label = getattr(indicator, "label", None)
    if isinstance(label, str):
        return label

    # func_object is an instance attribute — check the instance, not the type
    if hasattr(indicator, "func_object"):  # talib
        name = indicator.info.get("name")
        params = [repr(v) for v in indicator.parameters.values()]
        return f"{name}({', '.join(params)})"

    if is_polars_expr(indicator):
        try:
            return indicator.meta.output_name()
        except Exception:
            pass

    return repr(indicator)



def _is_default(v, default):
    """Safe equality check for short_repr — avoids non-bool returns from e.g. polars Expr."""
    if v is default:
        return True
    if default is None or not isinstance(default, (int, float, str, bool)):
        return False
    try:
        result = v == default
        return bool(result) if isinstance(result, bool) else False
    except Exception:
        return False


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

        if _is_default(v, p.default):
            if keyword_only or not isinstance(v, (int, float)):
                keyword_only = True
                continue

        if keyword_only:
            args.append(f"{p.name}={v!r}")
        else:
            args.append(f"{v!r}")

    args = ", ".join(args)

    return f"{cname}({args})"
