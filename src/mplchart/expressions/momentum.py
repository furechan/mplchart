"""Momentum expression factories"""

import polars as pl

from .prelude import wrap_expression, OPEN, HIGH, LOW, CLOSE, VOLUME
from .trend import EMA, SMA, RMA
from .volatility import ATR


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
    ups   = RMA(period, src=diff.clip(lower_bound=0))
    downs = RMA(period, src=(-diff).clip(lower_bound=0))
    return 100.0 - (100.0 / (1.0 + ups / downs))


@wrap_expression
def PPO(n1: int = 12, n2: int = 26, n3: int = 9, *, src: pl.Expr = CLOSE) -> tuple[pl.Expr, pl.Expr, pl.Expr]:
    """Price Percentage Oscillator — returns (ppo, signal, hist)"""
    ppo    = (EMA(n1, src=src) / EMA(n2, src=src) - 1) * 100
    signal = EMA(n3, src=ppo)
    hist   = ppo - signal
    return ppo.alias("ppo"), signal.alias("pposignal"), hist.alias("ppohist")


@wrap_expression
def MACD(n1: int = 12, n2: int = 26, n3: int = 9, *, src: pl.Expr = CLOSE) -> tuple[pl.Expr, pl.Expr, pl.Expr]:
    """Moving Average Convergence Divergence — returns (macd, signal, hist)"""
    macd   = EMA(n1, src=src) - EMA(n2, src=src)
    signal = EMA(n3, src=macd)
    hist   = macd - signal
    return macd.alias("macd"), signal.alias("macdsignal"), hist.alias("macdhist")


@wrap_expression
def BOP(period: int = 14, *, open: pl.Expr = OPEN, high: pl.Expr = HIGH, low: pl.Expr = LOW, close: pl.Expr = CLOSE) -> pl.Expr:
    """Balance of Power"""
    return SMA(period, src=(close - open) / (high - low))


@wrap_expression
def MACDV(n1: int = 12, n2: int = 26, n3: int = 9,
          *, high: pl.Expr = HIGH, low: pl.Expr = LOW, close: pl.Expr = CLOSE) -> tuple[pl.Expr, pl.Expr, pl.Expr]:
    """MACD Volatility-Normalized — returns (macd, signal, hist)"""
    macd   = (EMA(n1, src=close) - EMA(n2, src=close)) / ATR(n2, high=high, low=low, close=close) * 100
    signal = EMA(n3, src=macd)
    hist   = macd - signal
    return macd.alias("macd"), signal.alias("macdsignal"), hist.alias("macdhist")


@wrap_expression
def CMF(period: int = 20,
        *, high: pl.Expr = HIGH, low: pl.Expr = LOW, close: pl.Expr = CLOSE, volume: pl.Expr = VOLUME) -> pl.Expr:
    """Chaikin Money Flow"""
    mfv = (2 * close - high - low) / (high - low) * volume
    return mfv.rolling_sum(period) / volume.rolling_sum(period)


@wrap_expression
def MFI(period: int = 14,
        *, high: pl.Expr = HIGH, low: pl.Expr = LOW, close: pl.Expr = CLOSE, volume: pl.Expr = VOLUME) -> pl.Expr:
    """Money Flow Index"""
    typ   = (high + low + close) / 3
    flow  = typ * volume * typ.diff().sign()
    pflow = flow.clip(lower_bound=0).rolling_sum(period)
    nflow = (-flow).clip(lower_bound=0).rolling_sum(period)
    return 100 - 100 / (1 + pflow / nflow)


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
