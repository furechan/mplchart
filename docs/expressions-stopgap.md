# Expressions vs Indicators — Stopgap Analysis

_Last updated: 2026-04-17_

## In both (parity)

`ADX`, `ATR`, `BBANDS`, `BBP`, `BBW`, `BOP`, `CMF`, `DEMA`, `DMI`, `DONCHIAN`, `EMA`, `HMA`, `KELTNER`, `MACD`, `MACDV`, `MFI`, `NATR`, `PPO`, `ROC`, `RSI`, `SMA`, `STOCH`, `TEMA`, `WMA`

## In indicators only (missing from expressions)

None — all remaining indicators have expression equivalents.

`SLOPE`, `TSF`, `RVALUE`, `CURVE`, and `QSF` (the regression family) were removed
from indicators entirely: they require `rolling_map` / `rolling().apply()` with no
native vectorized path in either Polars or pandas. `ALMA` was also removed from
indicators and preserved in `playground/alma-indicator.ipynb` pending a decision
on whether to add it as an expression.

## In expressions only (no indicator equivalent)

These are building blocks or price transforms, not standalone indicators:

| Name | Notes |
|------|-------|
| `MIDPRICE` | (high + low) / 2 |
| `TYPPRICE` | (high + low + close) / 3 |
| `WCLPRICE` | (high + low + close×2) / 4 |
| `TRANGE` | True Range (sub-expression used by ATR) |
| `MOM` | Raw momentum (close − close[n]) |
| `RMA` | Wilder/RMA smoothing (used internally) |
