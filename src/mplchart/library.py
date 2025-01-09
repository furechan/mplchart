"""technical analysis library"""

import math
import numpy as np
import pandas as pd


from .utils import get_series  # noqa F401

# TODO remove get_series import


def calc_price(prices, item):
    """get or compute price item from prices"""
    if item in prices:
        return prices[item]

    if item in ("mid", "hl", "hl2"):
        return (prices["high"] + prices["low"]) / 2

    if item in ("typ", "hlc", "hlc3"):
        return (prices["high"] + prices["low"] + prices["close"]) / 3

    if item in ("wcl", "hlcc", "hlcc4"):
        return (prices["high"] + prices["low"] + prices["close"] * 2) / 4

    if item in ("avg", "ohlc", "ohlc4"):
        return (prices["open"] + prices["high"] + prices["low"] + prices["close"]) / 4

    raise ValueError(f"Invalid price item {item!r}")


def calc_roc(series, period: int = 1):
    """Rate of Change"""
    return series.pct_change(period)


def calc_sma(series, period: int = 20):
    """Simple Moving Average"""
    return series.rolling(window=period).mean()


def calc_ema(series, period: int = 20):
    """Exponential Moving Average"""
    return series.ewm(
        span=period, min_periods=period, adjust=False, ignore_na=True
    ).mean()


def calc_rma(series, period: int = 14):
    """Rolling Moving Average (RSI style)"""
    return series.ewm(
        alpha=1 / period, min_periods=period, adjust=True, ignore_na=True
    ).mean()


def calc_mad(series, period: int = 14):
    """Rolling Mean Absolute Deviation"""
    diff = series - series.rolling(window=period).mean()
    return diff.abs().rolling(window=period).mean()


def calc_wma(series, period: int = 20):
    """Weighted Moving Average"""
    weights = np.arange(1, period + 1, dtype=float)
    weights /= np.sum(weights)

    def average(data):
        return np.sum(data.values * weights)

    return series.rolling(period).apply(average)


def calc_hma(series, period: int = 20):
    """Hull Moving Average"""

    if period <= 0:
        raise ValueError("period must be greater than zero")

    m1 = calc_wma(series, round(period / 2))
    m2 = calc_wma(series, period)
    m3 = (2 * m1) - m2

    result = calc_wma(m3, round(math.sqrt(period)))

    return result


def calc_alma(series, window: int = 9, offset: float = 0.85, sigma: float = 6.0):
    """Arnaud Legoux Moving Average"""
    m = offset * (window - 1)
    s = window / sigma
    w = np.array([np.exp(-((i - m) ** 2) / (2 * s**2)) for i in range(window)])
    w = w / w.sum()
    res = np.correlate(series, w, "valid")
    res = np.insert(res, 0, [np.nan] * (window - 1))
    return pd.Series(res, index=series.index)


def calc_rsi(series, period: int = 14):
    """Relative Strength Index"""
    ewm = dict(alpha=1.0 / period, min_periods=period, adjust=True, ignore_na=True)

    diff = series.diff()
    ups = diff.clip(lower=0).ewm(**ewm).mean()
    downs = diff.clip(upper=0).abs().ewm(**ewm).mean()
    result = 100.0 - (100.0 / (1.0 + ups / downs))
    return result


def calc_cci(prices, period: int = 20):
    """Commodity Channel Index"""

    prc = calc_price(prices, "hlc")
    sma = calc_sma(prc, period)
    div = calc_mad(prc, period) * 0.015
    return (prc - sma) / div


def calc_bop(prices, period: int = 20):
    """Balance of Power"""

    bop = (prices.close - prices.open) / (prices.high - prices.low)
    return calc_sma(bop, period)


def calc_cmf(prices, period: int = 20):
    """Chaiking Money Flow"""

    mult = (2 * prices.close - prices.high - prices.low) / (prices.high - prices.low) * prices.volume
    num = mult.rolling(window=period).sum()
    div = prices.volume.rolling(window=period).sum()
    return num / div


def calc_mfi(prices, period: int = 14):
    """Money Flow Index"""
    prc = calc_price(prices, "hlc")

    flow = prc * prices.volume * np.sign(prc.diff(1))
    pflow = np.clip(flow, 0.0, None)
    nflow = -np.clip(flow, None, 0.0)

    ratio = pflow.rolling(window=period).sum() / nflow.rolling(window=period).sum()

    result = 100 - 100 / (1 + ratio)

    return result


def calc_atr(prices, period: int = 14, *, percent: bool = False):
    """Average True Range"""

    hlc = prices.filter(["high", "low"]).join(prices["close"].shift(1))
    trange = hlc.max(axis=1) - hlc.min(axis=1)

    if period > 0:
        ewm = dict(alpha=1 / period, min_periods=period, adjust=True, ignore_na=True)
        result = trange.ewm(**ewm).mean()
    else:
        result = trange

    if percent:
        result = 100 * result / prices["close"]

    return result


def calc_macd(series, n1: int = 20, n2: int = 26, n3: int = 9):
    """Moving Average Convergence Divergence"""
    ema1 = calc_ema(series, n1)
    ema2 = calc_ema(series, n2)
    macd = ema1 - ema2
    signal = calc_ema(macd, n3)
    hist = macd - signal

    result = dict(macd=macd, macdsignal=signal, macdhist=hist)
    result = pd.DataFrame(result)
    return result


def calc_ppo(series, n1: int = 20, n2: int = 26, n3: int = 9):
    """Price Percentage Oscillator"""
    ema1 = calc_ema(series, n1)
    ema2 = calc_ema(series, n2)
    ppo = (ema1 / ema2 - 1) * 100
    signal = calc_ema(ppo, n3)
    hist = ppo - signal

    result = dict(ppo=ppo, pposignal=signal, ppohist=hist)
    return pd.DataFrame(result)


def calc_dmi(prices, period: int = 14):
    """Directional Movement Index"""

    ewm = dict(alpha=1 / period, min_periods=period, adjust=True, ignore_na=True)

    atr = calc_atr(prices, period)

    hm = prices.high.diff(1)
    lm = -prices.low.diff(1)

    pdm = hm.where((hm > lm) & (hm > 0), 0)
    ndm = lm.where((lm > hm) & (lm > 0), 0)

    pdi = 100 * pdm.ewm(**ewm).mean() / atr
    ndi = 100 * ndm.ewm(**ewm).mean() / atr

    dx = 100 * np.abs(pdi - ndi) / (pdi + ndi)
    adx = dx.ewm(**ewm).mean()

    result = dict(adx=adx, pdi=pdi, ndi=ndi)
    result = pd.DataFrame(result)

    return result


def calc_adx(prices, period: int = 14):
    """Average Directional Index"""

    return calc_dmi(prices, period).adx


def calc_pdi(prices, period: int = 14):
    """Positive Directional Indicator"""

    return calc_dmi(prices, period).pdi


def calc_ndi(prices, period: int = 14):
    """Negative Directional Indicator"""

    return calc_dmi(prices, period).ndi


def calc_slope(series, period: int = 20):
    """Slope (time linear regression)"""

    xx = np.arange(period) - (period - 1) / 2.0

    def func(xs):
        if np.any(np.isnan(xs)):
            return np.nan

        return np.polyfit(xx, xs, 1)[0]

    return series.rolling(window=period).apply(func, raw=True)


def calc_tsf(series, period: int = 20, offset: int = 0):
    """Time series forecast (time linear regression)"""

    xx = np.arange(period) - (period - 1) / 2.0
    xo = xx[-1] + offset

    def func(xs):
        if np.any(np.isnan(xs)):
            return np.nan
        a, b = np.polyfit(xx, xs, 1)
        return a * xo + b

    return series.rolling(window=period).apply(func, raw=True)


def calc_rvalue(series, period: int = 20):
    """R-Value (time linear regression)"""

    xx = np.arange(period) - (period - 1) / 2.0

    def func(xs):
        if np.any(np.isnan(xs)):
            return np.nan

        return np.corrcoef(xx, xs)[0, 1]

    return series.rolling(window=period).apply(func, raw=True)


def calc_stoch(prices, period: int = 14, fastn: int = 3, slown: int = 3):
    """Stochastic Oscillator"""

    high = prices["high"].rolling(period).max()
    low = prices["low"].rolling(period).min()
    close = prices["close"]

    fastk = (close - low) / (high - low) * 100
    slowk = calc_sma(fastk, fastn)
    slowd = calc_sma(slowk, slown)

    slowk = fastk.rolling(window=fastn).mean()
    slowd = slowk.rolling(window=slown).mean()

    return pd.DataFrame(dict(slowk=slowk, slowd=slowd))


def calc_bbands(prices, period: int = 20, nbdev: float = 2.0):
    """Bollinger Bands"""
    midprc = (prices["high"] + prices["low"] + prices["close"]) / 3.0
    std = midprc.rolling(period).std(ddof=0)
    middle = midprc.rolling(period).mean()
    upper = middle + nbdev * std
    lower = middle - nbdev * std

    result = dict(upperband=upper, middleband=middle, lowerband=lower)
    return pd.DataFrame(result)


def calc_keltner(prices, period: int = 20, nbatr: float = 2.0):
    """Keltner Channel"""

    midprc = (prices["high"] + prices["low"] + prices["close"]) / 3.0
    atr = calc_atr(prices, period)
    middle = calc_ema(midprc, period)
    upper = middle + nbatr * atr
    lower = middle - nbatr * atr

    result = dict(upperband=upper, middleband=middle, lowerband=lower)
    return pd.DataFrame(result)
