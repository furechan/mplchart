"""technical analysis indicators — pandas pipeline only"""

from . import library

from .model import Indicator


class SMA(Indicator):
    """Simple Moving Average.

    Computes the arithmetic mean of the close price over a rolling window.
    Plotted on the same scale as the price series.

    Args:
        period (int): Number of bars in the rolling window. Defaults to 20.
    """


    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_sma(series, self.period)


class EMA(Indicator):
    """Exponential Moving Average.

    Computes the EMA using a smoothing factor of ``2 / (period + 1)``.
    Plotted on the same scale as the price series.

    Args:
        period (int): Span for the exponential smoothing. Defaults to 20.
    """


    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_ema(series, self.period)


class WMA(Indicator):
    """Weighted Moving Average.

    Computes a linearly weighted moving average giving more weight to recent bars.
    Plotted on the same scale as the price series.

    Args:
        period (int): Number of bars in the rolling window. Defaults to 20.
    """


    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_wma(series, self.period)


class HMA(Indicator):
    """Hull Moving Average.

    A weighted moving average that reduces lag by combining WMAs of different
    periods. Plotted on the same scale as the price series.

    Args:
        period (int): Number of bars in the rolling window. Defaults to 20.
    """


    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_hma(series, self.period)


class ALMA(Indicator):
    """Arnaud Legoux Moving Average.

    A Gaussian-weighted moving average that reduces lag while smoothing noise.
    Plotted on the same scale as the price series.

    Args:
        window (int): Number of bars in the rolling window. Defaults to 9.
        offset (float): Controls the trade-off between lag and smoothness,
            between 0 (minimum lag) and 1 (maximum smoothness). Defaults to 0.85.
        sigma (float): Controls the width of the Gaussian curve. Larger values
            produce a smoother result. Defaults to 6.0.
    """


    def __init__(self, window: int = 9, offset: float = 0.85, sigma: float = 6.0):
        self.window = window
        self.offset = offset
        self.sigma = sigma

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_alma(series, self.window, self.offset, self.sigma)


class ROC(Indicator):
    """Rate of Change.

    Measures the percentage change in price over a given number of bars.
    Positive values indicate upward momentum; negative values indicate downward momentum.

    Args:
        period (int): Lookback period in bars. Defaults to 20.
    """

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_roc(series, self.period)


class ATR(Indicator):
    """Average True Range.

    Measures market volatility as the rolling mean of the true range
    (the greatest of: current high minus low, absolute high minus previous close,
    absolute low minus previous close).

    Args:
        period (int): Smoothing period in bars. Defaults to 14.
    """

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_atr(prices, self.period)


class ATRP(Indicator):
    """Average True Range (percent).

    ATR expressed as a percentage of the closing price, making it comparable
    across instruments with different price levels.

    Args:
        period (int): Smoothing period in bars. Defaults to 14.
    """

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_atr(prices, self.period, percent=True)


class SLOPE(Indicator):
    """Slope of the linear regression line.

    Measures the rate of change of the linear regression fit over the lookback
    period. A positive slope indicates an uptrend; negative indicates a downtrend.

    Args:
        period (int): Lookback period for the linear regression. Defaults to 20.
    """

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_slope(series, self.period)

class CURVE(Indicator):
    """Curve of the quadratic regression line.

    Measures the curvature (second-derivative term) of a quadratic regression
    fit. Plotted as an area chart by default.

    Args:
        period (int): Lookback period for the quadratic regression. Defaults to 20.
    """

    line_style: str = "area"

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_curve(series, self.period)


class TSF(Indicator):
    """Time Series Forecast (Linear Regression).

    Projects the linear regression line forward (or backward) by ``offset`` bars.
    Plotted on the same scale as the price series.

    Args:
        period (int): Lookback period for the linear regression. Defaults to 20.
        offset (int): Number of bars to project forward from the end of the
            window. Use 0 for the current bar's fitted value. Defaults to 0.
    """


    def __init__(self, period: int = 20, offset: int = 0):
        self.period = period
        self.offset = offset

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_tsf(series, period=self.period, offset=self.offset)


class QSF(Indicator):
    """Quadratic Series Forecast (Quadratic Regression).

    Projects the quadratic regression curve forward (or backward) by ``offset``
    bars. Plotted on the same scale as the price series.

    Args:
        period (int): Lookback period for the quadratic regression. Defaults to 20.
        offset (int): Number of bars to project forward from the end of the
            window. Use 0 for the current bar's fitted value. Defaults to 0.
    """


    def __init__(self, period: int = 20, offset: int = 0):
        self.period = period
        self.offset = offset

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_qsf(series, period=self.period, offset=self.offset)


class RVALUE(Indicator):
    """R-Value of the linear regression.

    Returns the R² (coefficient of determination) of the linear regression fit,
    ranging from 0 (no fit) to 1 (perfect fit). Useful as a trend-strength filter.

    Args:
        period (int): Lookback period for the linear regression. Defaults to 20.
    """

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_rvalue(series, self.period)


class RSI(Indicator):
    """Relative Strength Index.

    Momentum oscillator that measures the speed and magnitude of recent price
    changes. Values range from 0 to 100. Traditionally, readings above 70
    indicate overbought conditions and readings below 30 indicate oversold
    conditions. Displayed in a separate pane above the main chart by default.

    Args:
        period (int): Smoothing period in bars. Defaults to 14.
    """

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_rsi(series, self.period)



class CCI(Indicator):
    """Commodity Channel Index.

    Oscillator that measures the deviation of price from its statistical mean.
    Values above +100 may signal overbought conditions; values below -100 may
    signal oversold conditions.

    Args:
        period (int): Lookback period in bars. Defaults to 20.
    """

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        return library.calc_cci(prices, self.period)


class BOP(Indicator):
    """Balance of Power.

    Measures the strength of buyers versus sellers by comparing the close-to-open
    move against the high-low range, smoothed over the given period.

    Args:
        period (int): Smoothing period in bars. Defaults to 14.
    """

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_bop(prices, self.period)


class CMF(Indicator):
    """Chaikin Money Flow.

    Oscillator that combines price and volume to measure the buying and selling
    pressure over a rolling window. Positive values indicate accumulation;
    negative values indicate distribution. Plotted as an area chart by default.

    Args:
        period (int): Lookback period in bars. Defaults to 20.
    """

    line_style: str = "area"

    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        return library.calc_cmf(prices, self.period)


class MFI(Indicator):
    """Money Flow Index.

    Volume-weighted RSI that measures buying and selling pressure. Values range
    from 0 to 100. Readings above 80 may indicate overbought conditions;
    readings below 20 may indicate oversold conditions.

    Args:
        period (int): Lookback period in bars. Defaults to 14.
    """

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_mfi(prices, self.period)



class ADX(Indicator):
    """Average Directional Index.

    Measures trend strength regardless of direction. Values range from 0 to 100.
    Readings above 20–25 are typically considered trending; above 40 indicate a
    strong trend.

    Args:
        period (int): Smoothing period in bars. Defaults to 14.
    """

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_adx(prices, self.period)


class DMI(Indicator):
    """Directional Movement Index.

    Plots the positive (+DI) and negative (-DI) directional indicators together
    with the ADX. Crossovers of +DI and -DI signal potential trend changes.

    Args:
        period (int): Smoothing period in bars. Defaults to 14.
    """

    def __init__(self, period: int = 14):
        self.period = period

    def __call__(self, prices):
        return library.calc_dmi(prices, self.period)


class PPO(Indicator):
    """Price Percentage Oscillator.

    Measures the percentage difference between two EMAs of price. Returns a
    DataFrame with columns ``ppo`` (the oscillator line), ``signal`` (EMA of
    PPO), and ``histogram`` (PPO minus signal).

    Args:
        n1 (int): Period of the faster EMA. Defaults to 12.
        n2 (int): Period of the slower EMA. Defaults to 26.
        n3 (int): Period of the signal line EMA. Defaults to 9.
    """

    def __init__(self, n1: int = 12, n2: int = 26, n3: int = 9):
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_ppo(series, self.n1, self.n2, self.n3)


class MACD(Indicator):
    """Moving Average Convergence Divergence.

    Trend-following momentum indicator showing the relationship between two
    EMAs of price. Returns a DataFrame with columns ``macd`` (the difference
    between the fast and slow EMAs), ``signal`` (EMA of MACD), and
    ``histogram`` (MACD minus signal).

    Args:
        n1 (int): Period of the faster EMA. Defaults to 12.
        n2 (int): Period of the slower EMA. Defaults to 26.
        n3 (int): Period of the signal line EMA. Defaults to 9.
    """

    def __init__(self, n1: int = 12, n2: int = 26, n3: int = 9):
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_macd(series, self.n1, self.n2, self.n3)


class MACDV(Indicator):
    """Moving Average Convergence Divergence — Volatility Normalized.

    MACD variant where the histogram is normalized by the ATR, making it
    comparable across instruments with different volatility levels. Returns a
    DataFrame with columns ``macd``, ``signal``, and ``histogram``.

    Args:
        n1 (int): Period of the faster EMA. Defaults to 12.
        n2 (int): Period of the slower EMA. Defaults to 26.
        n3 (int): Period of the signal line EMA. Defaults to 9.
    """

    def __init__(self, n1: int = 12, n2: int = 26, n3: int = 9):
        self.n1 = n1
        self.n2 = n2
        self.n3 = n3

    def __call__(self, prices):
        return library.calc_macdv(prices, self.n1, self.n2, self.n3)


class STOCH(Indicator):
    """Stochastic Oscillator.

    Momentum indicator comparing the closing price to its price range over a
    lookback period. Returns a DataFrame with columns ``k`` (the fast %K line)
    and ``d`` (the slow %D signal line, a smoothed version of %K). Values range
    from 0 to 100.

    Args:
        period (int): Lookback period for the %K calculation. Defaults to 14.
        fastn (int): Smoothing period for the fast %K line. Defaults to 3.
        slown (int): Smoothing period for the slow %D signal line. Defaults to 3.
    """

    def __init__(self, period: int = 14, fastn: int = 3, slown: int = 3):
        self.period = period
        self.fastn = fastn
        self.slown = slown

    def __call__(self, prices):
        return library.calc_stoch(prices, self.period)


class BBANDS(Indicator):
    """Bollinger Bands.

    Volatility bands placed above and below a simple moving average. Returns a
    DataFrame with columns ``upper``, ``middle`` (the SMA), and ``lower``.
    Plotted on the same scale as the price series.

    Args:
        period (int): Period for the middle SMA and standard deviation calculation.
            Defaults to 20.
        nbdev (float): Number of standard deviations for the upper and lower bands.
            Defaults to 2.0.
    """


    def __init__(self, period: int = 20, nbdev: float = 2.0):
        self.period = period
        self.nbdev = nbdev

    def __call__(self, prices):
        return library.calc_bbands(prices, self.period, self.nbdev)


class BBP(Indicator):
    """Bollinger Bands Percent (%B).

    Measures where price sits within the Bollinger Bands, expressed as a
    fraction. A value of 1.0 means price is at the upper band; 0.0 means price
    is at the lower band; 0.5 means price is at the middle band.

    Args:
        period (int): Period for the SMA and standard deviation. Defaults to 20.
        nbdev (float): Number of standard deviations for the bands. Defaults to 2.0.
    """

    def __init__(self, period: int = 20, nbdev: float = 2.0):
        self.period = period
        self.nbdev = nbdev

    def __call__(self, prices):
        return library.calc_bbp(prices, self.period, self.nbdev)


class BBW(Indicator):
    """Bollinger Bands Width.

    Measures the width of the Bollinger Bands as a percentage of the middle band.
    Expanding width indicates increasing volatility; contracting width indicates
    a squeeze (low volatility period).

    Args:
        period (int): Period for the SMA and standard deviation. Defaults to 20.
        nbdev (float): Number of standard deviations for the bands. Defaults to 2.0.
    """

    def __init__(self, period: int = 20, nbdev: float = 2.0):
        self.period = period
        self.nbdev = nbdev

    def __call__(self, prices):
        return library.calc_bbw(prices, self.period, self.nbdev)



class KELTNER(Indicator):
    """Keltner Channel.

    Volatility-based envelope using an EMA as the middle band and ATR multiples
    as the upper and lower bands. Returns a DataFrame with columns ``upper``,
    ``middle``, and ``lower``. Plotted on the same scale as the price series.

    Args:
        period (int): Period for the EMA middle band and ATR calculation.
            Defaults to 20.
        nbatr (float): ATR multiplier for the upper and lower bands. Defaults to 2.0.
    """


    def __init__(self, period: int = 20, nbatr: float = 2.0):
        self.period = period
        self.nbatr = nbatr

    def __call__(self, prices):
        return library.calc_keltner(prices, period=self.period, nbatr=self.nbatr)


class DONCHIAN(Indicator):
    """Donchian Channel.

    Price envelope based on the highest high and lowest low over a rolling
    window. Returns a DataFrame with columns ``upper``, ``middle``, and
    ``lower``. Plotted on the same scale as the price series.

    Args:
        period (int): Lookback period in bars. Defaults to 20.
    """


    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        return library.calc_donchian(prices, period=self.period)


class DEMA(Indicator):
    """Double Exponential Moving Average.

    Reduces lag compared to a standard EMA by combining a single EMA and a
    double-smoothed EMA. Plotted on the same scale as the price series.

    Args:
        period (int): Span for the exponential smoothing. Defaults to 20.
    """


    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_dema(series, self.period)


class TEMA(Indicator):
    """Triple Exponential Moving Average.

    Further reduces lag compared to DEMA by combining single, double, and
    triple-smoothed EMAs. Plotted on the same scale as the price series.

    Args:
        period (int): Span for the exponential smoothing. Defaults to 20.
    """


    def __init__(self, period: int = 20):
        self.period = period

    def __call__(self, prices):
        series = self.get_series(prices)
        return library.calc_tema(series, self.period)


__all__ = [k for k in dir() if k.isupper()]
