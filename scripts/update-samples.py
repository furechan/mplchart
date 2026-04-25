"""Download and update bundled sample prices (AAPL OHLCV via yfinance)."""

from pathlib import Path
from functools import lru_cache
from typing import cast

import pandas as pd
import yfinance as yf  # type: ignore

ROOTDIR = Path(__file__).parent.parent
PKGDIR = ROOTDIR.joinpath("src/mplchart").resolve(strict=True)
SAMPLES = PKGDIR / "samples"

SYMBOL = "AAPL"

INTERVAL = dict(daily="1d", hourly="1h", minute="1m")
MAXPERIOD = dict(daily="max", hourly="2Y", minute="7d")

EXPECTED_COLUMNS = ["open", "high", "low", "close", "volume"]
EXPECTED_INDEX = dict(daily="date", hourly="datetime", minute="datetime")
MIN_ROWS = dict(daily=5000, hourly=500, minute=100)
NUMERIC_COLS = ["open", "high", "low", "close", "volume"]


def check(prices: pd.DataFrame, freq: str) -> None:
    errors = []

    if list(prices.columns) != EXPECTED_COLUMNS:
        errors.append(f"columns: expected {EXPECTED_COLUMNS}, got {list(prices.columns)}")

    expected_index = EXPECTED_INDEX[freq]
    if prices.index.name != expected_index:
        errors.append(f"index name: expected {expected_index!r}, got {prices.index.name!r}")

    for col in NUMERIC_COLS:
        if col in prices.columns and not pd.api.types.is_numeric_dtype(prices[col]):
            errors.append(f"column {col!r}: expected numeric, got {prices[col].dtype}")

    min_rows = MIN_ROWS[freq]
    if len(prices) < min_rows:
        errors.append(f"row count: expected >= {min_rows}, got {len(prices)}")

    if errors:
        raise ValueError(f"Sanity check failed for {freq}:\n" + "\n".join(f"  - {e}" for e in errors))


@lru_cache
def get_prices(symbol: str, *, freq: str = "daily") -> pd.DataFrame:
    interval = INTERVAL[freq]
    period = MAXPERIOD[freq]
    prices = yf.Ticker(symbol).history(interval=interval, period=period, auto_adjust=True)

    if prices is None or prices.empty:
        raise ValueError(f"No data found for {symbol!r} with freq={freq!r}")

    prices = prices.filter(["Open", "High", "Low", "Close", "Volume"])
    prices = prices.rename(columns=str.lower)

    prices.index.name = EXPECTED_INDEX[freq]

    if freq == "daily":
        prices.index = cast(pd.DatetimeIndex, prices.index).tz_localize(None)

    return prices


if __name__ == "__main__":
    for freq in INTERVAL:
        prices = get_prices(SYMBOL, freq=freq)
        check(prices, freq)
        fname = f"{freq}-prices.csv"
        outfile = SAMPLES / fname
        data = prices.to_csv(lineterminator="\n")
        print(f"Updating {outfile.name} ... ({len(prices)} rows)")
        outfile.write_text(data)
