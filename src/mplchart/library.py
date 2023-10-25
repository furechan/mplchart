""" technical analysis library """

import numpy as np
import pandas as pd


def get_series(prices, item: str = None):
    """ extracts series of given name if applicable """

    # rename columns to make search case insensitive
    prices = prices.rename(columns=str.lower)

    if item is not None:
        return prices[item.lower()]

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


def calc_slope(series, period: int = 20):
    """ calculates the slope (lnear regression) over a rolling window """

    xx = np.arange(period) - (period - 1) / 2.0

    def func(xs):
        if np.any(np.isnan(xs)):
            return np.nan

        return np.polyfit(xx, xs, 1)[0]

    return series.rolling(window=period).apply(func, raw=True)


def calc_bbands(prices, period: int = 20, nbdev: float = 2.0):
    """ Bollinger Bands """
    midprc = (prices['high'] + prices['low'] + prices['close']) / 3.0
    std = midprc.rolling(period).std(ddof=0)
    middle = midprc.rolling(period).mean()
    upper = middle + nbdev * std
    lower = middle - nbdev * std
    result = dict(upperband=upper, middleband=middle, lowerband=lower)
    result = pd.DataFrame(result)
    return result
