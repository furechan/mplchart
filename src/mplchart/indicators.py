""" technical analysis indicators """

from . import library

from .library import get_series

from dataclasses import dataclass

from typing import ClassVar


@dataclass
class SMA:
    """Simple Moving Average"""

    period: int = 20

    same_scale: ClassVar[bool] = True

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_sma(series, self.period)


@dataclass
class EMA:
    """Exponential Moving Average"""

    period: int = 20

    same_scale: ClassVar[bool] = True

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_ema(series, self.period)


@dataclass
class ROC:
    """Rate of Change"""

    period: int = 20

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_roc(series, self.period)


@dataclass
class RSI:
    """Relative Strengh Index"""

    period: int = 14

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_rsi(series, self.period)


@dataclass
class ATR:
    """Average True Range"""

    period: int = 14

    def __call__(self, prices):
        return library.calc_atr(prices, self.period)


@dataclass
class ADX:
    """Average Directional Index"""

    period: int = 14

    def __call__(self, prices):
        return library.calc_adx(prices, self.period)


@dataclass
class MACD:
    """Moving Average Convergence Divergence"""

    n1: int = 12
    n2: int = 26
    n3: int = 9

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_macd(series, self.n1, self.n2, self.n3)


@dataclass
class PPO:
    """Price Percentage Oscillator"""

    n1: int = 12
    n2: int = 26
    n3: int = 9

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_ppo(series, self.n1, self.n2, self.n3)


@dataclass
class SLOPE:
    """Slope (Linear regression with time)"""

    period: int = 20

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_slope(series, self.period)


@dataclass
class BBANDS:
    """Bollinger Bands"""

    period: int = 20
    nbdev: float = 2.0

    same_scale: ClassVar[bool] = True

    def __call__(self, prices):
        return library.calc_bbands(prices, self.period, self.nbdev)


__all__ = [k for k in dir() if k.isupper()]
