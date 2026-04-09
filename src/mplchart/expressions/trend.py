"""Trend expression factories"""

import polars as pl

from .prelude import wrap_expression, CLOSE


@wrap_expression
def SMA(period: int = 20, *, src: pl.Expr = CLOSE) -> pl.Expr:
    """Simple Moving Average"""
    return src.rolling_mean(period, min_samples=period)


@wrap_expression
def EMA(period: int = 20, *, src: pl.Expr = CLOSE) -> pl.Expr:
    """Exponential Moving Average"""
    return src.ewm_mean(span=period, min_samples=period)


@wrap_expression
def RMA(period: int = 14, *, src: pl.Expr = CLOSE) -> pl.Expr:
    """Rolling Moving Average (RSI style)"""
    return src.ewm_mean(alpha=1 / period, min_samples=period, adjust=True)


@wrap_expression
def WMA(period: int = 20, *, src: pl.Expr = CLOSE) -> pl.Expr:
    """Weighted Moving Average"""
    weights = list(range(1, period + 1))
    total = sum(weights)
    return src.rolling_sum(period, weights=[w / total for w in weights], min_samples=period)


@wrap_expression
def HMA(period: int = 20, *, src: pl.Expr = CLOSE) -> pl.Expr:
    """Hull Moving Average"""
    half = WMA(period // 2, src=src)
    full = WMA(period, src=src)
    diff = half * 2 - full
    return WMA(round(period ** 0.5), src=diff)


@wrap_expression
def DEMA(period: int = 20, *, src: pl.Expr = CLOSE) -> pl.Expr:
    """Double Exponential Moving Average"""
    ema1 = EMA(period, src=src)
    ema2 = EMA(period, src=ema1)
    return 2 * ema1 - ema2


@wrap_expression
def TEMA(period: int = 20, *, src: pl.Expr = CLOSE) -> pl.Expr:
    """Triple Exponential Moving Average"""
    ema1 = EMA(period, src=src)
    ema2 = EMA(period, src=ema1)
    ema3 = EMA(period, src=ema2)
    return 3 * (ema1 - ema2) + ema3
