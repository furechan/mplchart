"""Volatility expression factories"""

import polars as pl

from .prelude import wrap_expression, HIGH, LOW, CLOSE
from .trend import EMA


@wrap_expression
def TRANGE(*, high: pl.Expr = HIGH, low: pl.Expr = LOW, close: pl.Expr = CLOSE) -> pl.Expr:
    """True Range"""
    return (
        pl.max_horizontal(high, close.shift(1))
        - pl.min_horizontal(low, close.shift(1))
    )


@wrap_expression
def ATR(period: int = 14, *, high: pl.Expr = HIGH, low: pl.Expr = LOW, close: pl.Expr = CLOSE) -> pl.Expr:
    """Average True Range"""
    tr = TRANGE(high=high, low=low, close=close)
    return tr.ewm_mean(alpha=1 / period, min_samples=period, adjust=True)


@wrap_expression
def BBANDS(period: int = 20, nbdev: float = 2.0, *, src: pl.Expr = CLOSE) -> tuple[pl.Expr, pl.Expr, pl.Expr]:
    """Bollinger Bands — returns (upper, middle, lower)"""
    middle = src.rolling_mean(period, min_samples=period)
    std    = src.rolling_std(period, min_samples=period, ddof=0)
    upper  = middle + nbdev * std
    lower  = middle - nbdev * std
    return upper.alias("upperband"), middle.alias("middleband"), lower.alias("lowerband")


@wrap_expression
def DONCHIAN(period: int = 20, *, high: pl.Expr = HIGH, low: pl.Expr = LOW) -> tuple[pl.Expr, pl.Expr, pl.Expr]:
    """Donchian Channel — returns (upper, middle, lower)"""
    upper  = high.rolling_max(period)
    lower  = low.rolling_min(period)
    middle = (upper + lower) / 2
    return upper.alias("upperband"), middle.alias("middleband"), lower.alias("lowerband")


@wrap_expression
def KELTNER(period: int = 20, nbatr: float = 2.0,
            *, high: pl.Expr = HIGH, low: pl.Expr = LOW, close: pl.Expr = CLOSE) -> tuple[pl.Expr, pl.Expr, pl.Expr]:
    """Keltner Channel — returns (upper, middle, lower)"""
    midprc = (high + low + close) / 3
    atr    = ATR(period, high=high, low=low, close=close)
    middle = EMA(period, src=midprc)
    upper  = middle + nbatr * atr
    lower  = middle - nbatr * atr
    return upper.alias("upperband"), middle.alias("middleband"), lower.alias("lowerband")
