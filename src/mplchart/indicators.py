"""technical analysis indicators"""

from typing import List
from . import library

from .model import Indicator
from .utils import get_series
from .rsi_div_patterns import RsiDivergenceProperties, RsiDivergencePattern, find_rsi_divergences, calc_rsi
from .zigzag import Zigzag


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
    """Slope (Linear regression with time)"""

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_slope(series, self.period)


class RSI(Indicator):
    """Relative Strengh Index"""

    oversold: float = 30
    overbought: float = 70
    yticks: tuple = 30, 50, 70
    # default_pane: str = "above"

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        series = get_series(prices)
        return library.calc_rsi(series, self.period)

class RSIDIV(Indicator):
    """RSI Divergences"""
    def __init__(self, period: int = 14, backcandels: int = 2, forwardcandels: int = 2,
                 pivot_limit: int = 50,scan_props: RsiDivergenceProperties = None):
        self.period = period
        self.backcandels = backcandels
        self.forwardcandels = forwardcandels
        self.pivot_limit = pivot_limit
        self.scan_props = scan_props

    def __call__(self, prices):
        pass

    def calc_divergences(self, prices, patterns: List[RsiDivergencePattern]):
        zigzag = Zigzag(backcandels=self.backcandels,
                        forwardcandels=self.forwardcandels,
                        pivot_limit=self.pivot_limit,
                        offset=0)
        zigzag.calculate(prices)
        rsi = calc_rsi(prices)
        # Find patterns
        for i in range(self.scan_props.offset, len(zigzag.zigzag_pivots)):
            find_rsi_divergences(zigzag, i, self.scan_props, patterns, rsi)

    def plot_handler(self, prices, chart):
        ax = chart.get_axes()
        # Initialize pattern storage
        patterns: List[RsiDivergencePattern] = []

        self.calc_divergences(prices, patterns)
        for pattern in patterns:
            # Use data.index to get the correct x positions
            line_x = [pattern.divergence_line.p1.index, pattern.divergence_line.p2.index]
            line_y = [pattern.divergence_line.p1.price, pattern.divergence_line.p2.price]

            if pattern.pattern_type == 1 or pattern.pattern_type == 3:
                color = "green"
            else:
                color = "red"
            ax.plot(line_x, line_y, color=color)
            if pattern.pivots[0].direction > 0:
                text_y = line_y[0] * 1.2
            else:
                text_y = line_y[0] * 0.8
            ax.annotate(pattern.pattern_name, (line_x[0], text_y), color=color)
            # annotate line points
            ax.annotate(line_x[0], (line_x[0], line_y[0]), color=color)
            ax.annotate(line_x[1], (line_x[1], line_y[1]), color=color)


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
    """Stochastik Oscillator"""

    def __init__(self, period: int = 14, fastn: int = 3, slown: int = 3):
        self.period = period
        self.fastn = fastn
        self.slown = slown

    def __call__(self, prices):
        return library.calc_stoch(prices, self.period)



__all__ = [k for k in dir() if k.isupper()]
