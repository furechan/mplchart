"""Volatility expression factories"""

import polars as pl

from .prelude import wrap_expression, HIGH, LOW, CLOSE
from .trend import EMA, RMA


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
    return RMA(period, src=tr)


@wrap_expression
def BBP(period: int = 20, nbdev: float = 2.0, *, src: pl.Expr = CLOSE) -> pl.Expr:
    """Bollinger Bands Percent (%B)"""
    middle = src.rolling_mean(period, min_samples=period)
    std    = src.rolling_std(period, min_samples=period, ddof=0)
    upper  = middle + nbdev * std
    lower  = middle - nbdev * std
    return (src - lower) / (upper - lower) * 100


@wrap_expression
def BBW(period: int = 20, nbdev: float = 2.0, *, src: pl.Expr = CLOSE) -> pl.Expr:
    """Bollinger Bands Width"""
    middle = src.rolling_mean(period, min_samples=period)
    std    = src.rolling_std(period, min_samples=period, ddof=0)
    upper  = middle + nbdev * std
    lower  = middle - nbdev * std
    return (upper - lower) / middle * 100


@wrap_expression
def NATR(period: int = 14, *, high: pl.Expr = HIGH, low: pl.Expr = LOW, close: pl.Expr = CLOSE) -> pl.Expr:
    """Normalized Average True Range (percent)"""
    return ATR(period, high=high, low=low, close=close) / close * 100


@wrap_expression
def DMI(period: int = 14, *, high: pl.Expr = HIGH, low: pl.Expr = LOW, close: pl.Expr = CLOSE) -> pl.Expr:
    """Directional Movement Index — struct of (adx, pdi, ndi)"""
    atr = ATR(period, high=high, low=low, close=close)
    hm  = high.diff()
    lm  = -low.diff()
    pdm = pl.when((hm > lm) & (hm > 0)).then(hm).otherwise(0)
    ndm = pl.when((lm > hm) & (lm > 0)).then(lm).otherwise(0)
    pdi = 100 * pdm.ewm_mean(alpha=1/period, min_samples=period, adjust=True) / atr
    ndi = 100 * ndm.ewm_mean(alpha=1/period, min_samples=period, adjust=True) / atr
    dx  = 100 * (pdi - ndi).abs() / (pdi + ndi)
    adx = dx.ewm_mean(alpha=1/period, min_samples=period, adjust=True)
    return pl.struct(adx.alias("adx"), pdi.alias("pdi"), ndi.alias("ndi"))


@wrap_expression
def ADX(period: int = 14, *, high: pl.Expr = HIGH, low: pl.Expr = LOW, close: pl.Expr = CLOSE) -> pl.Expr:
    """Average Directional Index"""
    return DMI(period, high=high, low=low, close=close).struct.field("adx")


@wrap_expression
def BBANDS(period: int = 20, nbdev: float = 2.0, *, src: pl.Expr = CLOSE) -> pl.Expr:
    """Bollinger Bands — struct of (upperband, middleband, lowerband)"""
    middle = src.rolling_mean(period, min_samples=period)
    std    = src.rolling_std(period, min_samples=period, ddof=0)
    upper  = middle + nbdev * std
    lower  = middle - nbdev * std
    return pl.struct(upper.alias("upperband"), middle.alias("middleband"), lower.alias("lowerband"))


@wrap_expression
def DONCHIAN(period: int = 20, *, high: pl.Expr = HIGH, low: pl.Expr = LOW) -> pl.Expr:
    """Donchian Channel — struct of (upperband, middleband, lowerband)"""
    upper  = high.rolling_max(period)
    lower  = low.rolling_min(period)
    middle = (upper + lower) / 2
    return pl.struct(upper.alias("upperband"), middle.alias("middleband"), lower.alias("lowerband"))


@wrap_expression
def KELTNER(period: int = 20, nbatr: float = 2.0,
            *, high: pl.Expr = HIGH, low: pl.Expr = LOW, close: pl.Expr = CLOSE) -> pl.Expr:
    """Keltner Channel — struct of (upperband, middleband, lowerband)"""
    midprc = (high + low + close) / 3
    atr    = ATR(period, high=high, low=low, close=close)
    middle = EMA(period, src=midprc)
    upper  = middle + nbatr * atr
    lower  = middle - nbatr * atr
    return pl.struct(upper.alias("upperband"), middle.alias("middleband"), lower.alias("lowerband"))
