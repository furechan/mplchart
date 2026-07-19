"""Price expression factories"""

import polars as pl

from .prelude import wrap_expression, OPEN, HIGH, LOW, CLOSE


@wrap_expression
def MEDPRICE(*, high: pl.Expr = HIGH, low: pl.Expr = LOW) -> pl.Expr:
    """Median Price (HL/2)"""
    return (high + low) / 2


@wrap_expression
def AVGPRICE(*, open: pl.Expr = OPEN, high: pl.Expr = HIGH, low: pl.Expr = LOW, close: pl.Expr = CLOSE) -> pl.Expr:
    """Average Price (OHLC/4)"""
    return (open + high + low + close) / 4


@wrap_expression
def TYPPRICE(*, high: pl.Expr = HIGH, low: pl.Expr = LOW, close: pl.Expr = CLOSE) -> pl.Expr:
    """Typical Price (HLC/3)"""
    return (high + low + close) / 3


@wrap_expression
def WCLPRICE(*, high: pl.Expr = HIGH, low: pl.Expr = LOW, close: pl.Expr = CLOSE) -> pl.Expr:
    """Weighted Close Price (HLCC/4)"""
    return (high + low + close * 2) / 4
