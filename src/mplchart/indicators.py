""" Stockchart basic indicators """

import pandas as pd

from dataclasses import dataclass

from typing import ClassVar


def get_series(prices, item=None):
    """ extracts series of given name if applicable """
    if item is not None:
        return prices[item]

    if isinstance(prices, pd.Series):
        return prices

    if isinstance(prices, pd.DataFrame):
        return prices['close']


def calc_roc(series, period: int = 1):
    """ Rate of Change """
    return series.pct_change(period)


def calc_sma(series, period: int = 20):
    """ Simple Moving Average """
    return series.rolling(window=period).mean()


def calc_ema(series, period: int = 20):
    """ Exponential Moving Average """
    return series.ewm(span=period, adjust=True, ignore_na=True, min_periods=period).mean()


def calc_rsi(series, period: int = 14):
    """ Relative Strength Index """
    kw = dict(alpha=1.0 / period, min_periods=period, adjust=True, ignore_na=True)

    diff = series.diff()
    ups = diff.clip(lower=0).ewm(**kw).mean()
    downs = diff.clip(upper=0).abs().ewm(**kw).mean()
    result = 100.0 - (100.0 / (1.0 + ups / downs))

    return result


def calc_macd(series, n1: int = 20, n2: int = 26, n3: int = 9):
    """ Moving Average Convergence Divergence """
    ema1 = calc_ema(series, n1)
    ema2 = calc_ema(series, n2)

    macd = ema1 - ema2
    signal = calc_ema(macd, n3)
    hist = macd - signal

    result = dict(macd=macd, macdsignal=signal, macdhist=hist)
    result = pd.DataFrame(result
                          )
    return result


def calc_ppo(series, n1: int = 20, n2: int = 26, n3: int = 9):
    """ Price Percentage Oscillator """
    ema1 = calc_ema(series, n1)
    ema2 = calc_ema(series, n2)

    ppo = (ema1 / ema2 - 1) * 100
    signal = calc_ema(ppo, n3)
    hist = ppo - signal

    result = dict(ppo=ppo, pposignal=signal, ppohist=hist)
    result = pd.DataFrame(result)
    return result


def calc_bbands(prices, period=20, nbdev=2.0):
    """ Bollinger Bands """
    midprc = (prices['high'] + prices['low'] + prices['close']) / 3.0
    std = midprc.rolling(period).std(ddof=0)
    middle = midprc.rolling(period).mean()
    upper = middle + nbdev * std
    lower = middle - nbdev * std
    result = dict(upperband=upper, middleband=middle, lowerband=lower)
    result = pd.DataFrame(result)
    return result


@dataclass
class SMA:
    """ Simple Moving Average """
    period: int = 20

    same_scale: ClassVar[bool] = True

    def __call__(self, prices):
        series = get_series(prices)
        return calc_sma(series, self.period)


@dataclass
class EMA:
    """ Exponential Moving Average """
    period: int = 20

    same_scale: ClassVar[bool] = True

    def __call__(self, prices):
        series = get_series(prices)
        return calc_ema(series, self.period)


@dataclass
class ROC:
    """ Rate of Change """
    period: int = 20

    def __call__(self, prices):
        series = get_series(prices)
        return calc_roc(series, self.period)


@dataclass
class RSI:
    """ Relative Strengh Index """
    period: int = 20

    def __call__(self, prices):
        series = get_series(prices)
        return calc_rsi(series, self.period)


@dataclass
class MACD:
    """ Moving Average Convergence Divergence """
    n1: int = 12
    n2: int = 26
    n3: int = 9

    def __call__(self, prices):
        series = get_series(prices)
        return calc_macd(series, self.n1, self.n2, self.n3)


@dataclass
class PPO:
    """ Price Percentage Oscillator """
    n1: int = 12
    n2: int = 26
    n3: int = 9

    def __call__(self, prices):
        series = get_series(prices)
        return calc_ppo(series, self.n1, self.n2, self.n3)


@dataclass
class BBANDS:
    """ Bollinger Bands """
    period: int = 20
    nbdev: float = 2.0

    same_scale: ClassVar[bool] = True

    def __call__(self, prices):
        return calc_bbands(prices, self.period, self.nbdev)


__all__ = [k for k in dir() if k.isupper()]
