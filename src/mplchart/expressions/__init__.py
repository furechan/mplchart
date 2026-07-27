"""Polars expression factories.

Each factory returns a native ``polars.Expr`` computing the indicator over
an OHLCV frame: ``prices.select(SMA(50))``. In charts, expressions are
passed to ``chart.plot(...)`` directly (auto-plotted) or bound to a
renderer primitive via ``@``, as in ``RSI(14) @ LinePlot()``. These are
the polars-pipeline counterparts of ``mplchart.indicators``.
"""

from .prelude import wrap_expression, OPEN, HIGH, LOW, CLOSE, VOLUME

from .trend import SMA, EMA, RMA, WMA, HMA, DEMA, TEMA

from .momentum import ROC, MOM, RSI, PPO, MACD, MACDV, BOP, CMF, MFI, STOCH

from .volatility import TRANGE, ATR, BBP, BBW, NATR, BBANDS, DONCHIAN, KELTNER, DMI, ADX

from .prices import AVGPRICE, MEDPRICE, TYPPRICE, WCLPRICE

__all__ = [
    "wrap_expression",
    "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME",
    "SMA", "EMA", "RMA", "WMA", "HMA", "DEMA", "TEMA",
    "ROC", "MOM", "RSI", "PPO", "MACD", "MACDV", "BOP", "CMF", "MFI", "STOCH",
    "TRANGE", "ATR", "BBP", "BBW", "NATR", "BBANDS", "DONCHIAN", "KELTNER", "DMI", "ADX",
    "AVGPRICE", "MEDPRICE", "TYPPRICE", "WCLPRICE",
]
