"""pandas specific helpers for mplchart"""

import pandas as pd


def rebase_series(series, prices):
    """Rebase a series to start at the same level as prices.close.

    Drops NaNs from series, joins with prices to find the first common date,
    then scales the series so its value at that date matches prices.close.

    Args:
        series : Series  the series to rebase
        prices : DataFrame  reference prices with a 'close' column

    Returns:
        Series scaled to match prices.close at the first common date
    """
    
    close, values=prices["close"].align(series.dropna(), join="inner")

    if len(values):
        factor = close.iloc[0] / values.iloc[0]
        return series * factor
    else:
        return series


def merge_prices(prices, rebase=False, **kwargs):
    """Merge additional price series into a prices DataFrame.

    Appends one named column per kwarg, taken from the close price of each
    DataFrame. pandas aligns on the index, so dates missing from any series
    will be NaN. Use rebase=True to scale each series to the same starting
    level as prices.close at the first common date.

    Args:
        prices       : DataFrame  primary prices (all columns preserved)
        rebase (bool): if True, scale each added series to match prices.close
        **kwargs     : additional named price DataFrames

    Returns:
        DataFrame with all original columns plus one column per kwarg.

    Example:
        merge_prices(prices, aapl=prices_aapl, msft=prices_msft, rebase=True)
    """
    extra = {}
    
    for name, series in kwargs.items():
        if isinstance(series, pd.DataFrame):
            if "close" not in series.columns:
                raise ValueError(f"Expected a 'close' column in {name} DataFrame")
            series = series["close"]
        if rebase:
            series = rebase_series(series, prices)
        extra[name] = series

    return prices.assign(**extra)


