"""technical analysis indicators"""

from . import library

from .model import Indicator
from .utils import get_series


class SMA(Indicator):
    """Simple Moving Average"""

    same_scale: bool = True

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_sma(series, self.period)


class EMA(Indicator):
    """Exponential Moving Average"""

    same_scale: bool = True

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_ema(series, self.period)


class WMA(Indicator):
    """Weighted Moving Average"""

    same_scale: bool = True

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_wma(series, self.period)


class HMA(Indicator):
    """Hull Moving Average"""

    same_scale: bool = True

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_hma(series, self.period)


class ROC(Indicator):
    """Rate of Change"""

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_roc(series, self.period)


class ATR(Indicator):
    """Average True Range"""

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_atr(prices, self.period)


class ATRP(Indicator):
    """Average True Range (Percent)"""

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_atr(prices, self.period, percent=True)


class SLOPE(Indicator):
    """Slope (Time linear regression)"""

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_slope(series, self.period)


class RVALUE(Indicator):
    """RValue (Time linear regression)"""

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_rvalue(series, self.period)


class RSI(Indicator):
    """Relative Strengh Index"""

    oversold: float = 30
    overbought: float = 70
    yticks: tuple = 30, 50, 70
    default_pane: str = "above"

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_rsi(series, self.period)


class ADX(Indicator):
    """Average Directinal Index"""

    yticks: tuple = 20, 40

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_adx(prices, self.period)


class DMI(Indicator):
    """Directional Movement Index"""

    yticks: tuple = 20, 40

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_dmi(prices, self.period)


class MACD(Indicator):
    """Moving Average Convergence Divergence"""

    def __init__(self, n1: int = 12, n2: int = 26, n3: int = 9):
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_macd(series, self.n1, self.n2, self.n3)


class PPO(Indicator):
    """Price Percentage Oscillator"""

    def __init__(self, n1: int = 12, n2: int = 26, n3: int = 9):
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_ppo(series, self.n1, self.n2, self.n3)


class BBANDS(Indicator):
    """Bollinger Bands"""

    same_scale: bool = True

    def __init__(self, period: int = 20, nbdev: float = 2.0):
        self.period = period
        self.nbdev = nbdev

    def __call__(self, prices):
        return library.calc_bbands(prices, self.period, self.nbdev)


class STOCH(Indicator):
    """Stochastic Oscillator"""

    def __init__(self, period: int = 14, fastn: int = 3, slown: int = 3):
        self.period = period
        self.fastn = fastn
        self.slown = slown

    def __call__(self, prices):
        return library.calc_stoch(prices, self.period)



__all__ = [k for k in dir() if k.isupper()]
