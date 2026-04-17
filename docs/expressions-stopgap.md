# Expressions vs Indicators — Stopgap Analysis

_Last updated: 2026-04-17_

## In both (parity)

`ADX`, `ATR`, `BBANDS`, `BBP`, `BBW`, `BOP`, `CMF`, `DEMA`, `DMI`, `DONCHIAN`, `EMA`, `HMA`, `KELTNER`, `MACD`, `MACDV`, `MFI`, `NATR`, `PPO`, `ROC`, `RSI`, `SMA`, `STOCH`, `TEMA`, `WMA`

## In indicators only (missing from expressions)

| Name | Notes |
|------|-------|
| `SLOPE` | Rolling linear regression slope — no native Polars support |
| `TSF` | Rolling linear regression forecast — same constraint as SLOPE |
| `RVALUE` | Rolling R² — same constraint as SLOPE |
| `CURVE` | Rolling quadratic regression curvature — same constraint |
| `QSF` | Rolling quadratic forecast — same constraint |

All remaining gaps require either `rolling_map` (CCI) or a custom numpy rolling
implementation via `map_batches` (regression family). `ALMA` was also removed from
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
