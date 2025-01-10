"""technical analysis indicators"""

from . import library

from .model import Indicator


class SMA(Indicator):
    """Simple Moving Average"""

    same_scale: bool = True

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_sma(series, self.period)


class EMA(Indicator):
    """Exponential Moving Average"""

    same_scale: bool = True

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_ema(series, self.period)


class WMA(Indicator):
    """Weighted Moving Average"""

    same_scale: bool = True

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_wma(series, self.period)


class HMA(Indicator):
    """Hull Moving Average"""

    same_scale: bool = True

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_hma(series, self.period)


class ALMA(Indicator):
    """Arnaud Legoux Moving Average"""

    same_scale: bool = True

    def __init__(self, window: int = 9, offset: float = 0.85, sigma: float = 6.0):
        self.window = window
        self.offset = offset
        self.sigma = sigma

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_alma(series, self.window, self.offset, self.sigma)


class ROC(Indicator):
    """Rate of Change"""

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_roc(series, self.period)


class ATR(Indicator):
    """Average True Range"""

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_atr(prices, self.period)


class ATRP(Indicator):
    """Average True Range (percent)"""

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_atr(prices, self.period, percent=True)


class SLOPE(Indicator):
    """Slope (time linear regression)"""

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_slope(series, self.period)


class TSF(Indicator):
    """Time Siries Forecast (time linear regression)"""

    same_scale: bool = True

    def __init__(self, period: int = 20, offset: int =0):
        self.period = period
        self.offset = offset

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_tsf(series, period=self.period, offset=self.offset)


class RVALUE(Indicator):
    """R-Value (time linear regression)"""

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
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
        series = self.get_series(prices)
        return library.calc_rsi(series, self.period)



class CCI(Indicator):
    """Commodity Channel Index"""

    oversold: float = -100
    overbought: float = 100
    yticks: tuple = -100, 0, 100

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        return library.calc_cci(prices, self.period)


class BOP(Indicator):
    """Balance of Power"""

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        return library.calc_bop(prices, self.period)


class CMF(Indicator):
    """Chaikin Money Flow"""

    line_style: str = "area"

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        return library.calc_cmf(prices, self.period)


class MFI(Indicator):
    """Money Flow Index"""

    overbought: float = 80
    oversold: float = 20
    yticks: tuple = 20, 50, 80

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_mfi(prices, self.period)



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
        series = self.get_series(prices)
        return library.calc_macd(series, self.n1, self.n2, self.n3)


class PPO(Indicator):
    """Price Percentage Oscillator"""

    def __init__(self, n1: int = 12, n2: int = 26, n3: int = 9):
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_ppo(series, self.n1, self.n2, self.n3)


class STOCH(Indicator):
    """Stochastic Oscillator"""

    def __init__(self, period: int = 14, fastn: int = 3, slown: int = 3):
        self.period = period
        self.fastn = fastn
        self.slown = slown

    def __call__(self, prices):
        return library.calc_stoch(prices, self.period)


class BBANDS(Indicator):
    """Bollinger Bands"""

    same_scale: bool = True

    def __init__(self, period: int = 20, nbdev: float = 2.0):
        self.period = period
        self.nbdev = nbdev

    def __call__(self, prices):
        return library.calc_bbands(prices, self.period, self.nbdev)


class KELTNER(Indicator):
    """Keltner Channels"""

    same_scale: bool = True

    def __init__(self, period: int = 20, nbatr: float = 2.0):
        self.period = period
        self.nbatr = nbatr

    def __call__(self, prices):
        return library.calc_keltner(prices, period=self.period, nbatr = self.nbatr)


__all__ = [k for k in dir() if k.isupper()]
