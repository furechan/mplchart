"""Price expression factories"""

import polars as pl

from .prelude import wrap_expression, HIGH, LOW, CLOSE


@wrap_expression
def MIDPRICE(*, high: pl.Expr = HIGH, low: pl.Expr = LOW) -> pl.Expr:
    """Median Price (HL/2)"""
    return (high + low) / 2


@wrap_expression
def TYPPRICE(*, high: pl.Expr = HIGH, low: pl.Expr = LOW, close: pl.Expr = CLOSE) -> pl.Expr:
    """Typical Price (HLC/3)"""
    return (high + low + close) / 3


@wrap_expression
def WCLPRICE(*, high: pl.Expr = HIGH, low: pl.Expr = LOW, close: pl.Expr = CLOSE) -> pl.Expr:
    """Weighted Close Price (HLCC/4)"""
    return (high + low + close * 2) / 4
