"""Momentum expression factories"""

import polars as pl

from .prelude import wrap_expression, HIGH, LOW, CLOSE
from .trend import EMA, SMA


@wrap_expression
def ROC(period: int = 1, *, src: pl.Expr = CLOSE) -> pl.Expr:
    """Rate of Change"""
    return src.pct_change(period)


@wrap_expression
def MOM(period: int = 1, *, src: pl.Expr = CLOSE) -> pl.Expr:
    """Momentum"""
    return src - src.shift(period)


@wrap_expression
def RSI(period: int = 14, *, src: pl.Expr = CLOSE) -> pl.Expr:
    """Relative Strength Index"""
    diff  = src.diff()
    ups   = diff.clip(lower_bound=0).ewm_mean(alpha=1 / period, min_samples=period, adjust=True)
    downs = (-diff).clip(lower_bound=0).ewm_mean(alpha=1 / period, min_samples=period, adjust=True)
    return 100.0 - (100.0 / (1.0 + ups / downs))


@wrap_expression
def MACD(n1: int = 12, n2: int = 26, n3: int = 9, *, src: pl.Expr = CLOSE) -> tuple[pl.Expr, pl.Expr, pl.Expr]:
    """Moving Average Convergence Divergence — returns (macd, signal, hist)"""
    macd   = EMA(n1, src=src) - EMA(n2, src=src)
    signal = EMA(n3, src=macd)
    hist   = macd - signal
    return macd.alias("macd"), signal.alias("macdsignal"), hist.alias("macdhist")


@wrap_expression
def STOCH(period: int = 14, fastn: int = 3, slown: int = 3,
          *, high: pl.Expr = HIGH, low: pl.Expr = LOW, src: pl.Expr = CLOSE) -> tuple[pl.Expr, pl.Expr]:
    """Stochastic Oscillator — returns (slowk, slowd)"""
    highest = high.rolling_max(period)
    lowest  = low.rolling_min(period)
    fastk   = (src - lowest) / (highest - lowest) * 100
    slowk   = SMA(fastn, src=fastk)
    slowd   = SMA(slown, src=slowk)
    return slowk.alias("slowk"), slowd.alias("slowd")
