# Change Log

## 0.0.26
- Multi source logic will be removed. Merge/rebase data before plotting see rebase-series.ipynb example
- Chart `rebase` option and `rebase_data` has been deprecated
- Added `pandas` helper module for merging/rebasing pandas series

## 0.0.25
- Python-rewquires >= 10
- Added `MACDV` Indicator (MACD - Volatility Normalized)

## 0.0.24
- Swithed to ub-build backend
- Added `BBP` Indicator (Bollinger Bands Percent)
- Added `BBW` Indicator (Bollinger Bands Width)


## 0.0.23
- Added `QSF` Indicator (Quadratic Series Forecast)
- Added `CURVE` Indicator (Quadratic Regression)
- Added `DEMA` Indicator (Double Exponential Moving Average)
- Added `TEMA` Indicator (Triple Exponential Moving Average)
- Switched to `tox.toml`

## 0.0.22
- Added `DONCHIAN` Indicator (Donchian Channel)

## 0.0.21
- Refactored `wrappers.py` into `plotters.py`
- Single line indicators now accept a `line_style` attribute

## 0.0.20
- Added `CCI` Indicator (Commodity Channel Index)
- Added `BOP` Indicator (Balance of Power)
- Added `CMF` Indicator (Chaikin Money Flow)
- Added `MFI` Indicator (Money Flow Index)

## 0.0.19
- Replacing chart `reindex` method with `slice`. The `reindex` method will be repurposed, do not use.

## 0.0.18
- Added `ZigZag` Primitive (Experimental)
- `Price` primitive now accepts calculation items like 'hlc', 'hlcc', ...
- `Price` can now be used and composed as an indicator like in `EMA(20) @ Price('hlcc')`

## 0.0.17
- Added `ALMA` Indicator (Arnaud Legoux Moving Average)
- Added `KELTNER` indicator (Keltner Channel)
- Added `get_series` method to `Indicator` as a wrapper to `utils.get_series`

## 0.0.16
- Added `TSF` Indicator (Time Series Forecast)
- Added `Markers` primitive 
- Deprecated `extract_df`. Use `reindex` instead

## 0.0.15
- Added `Stripes` primitive to plot vertical stripes depending on a flag value (experimental)
- Added `alpha` parameter to `Price`, `OHLC`, `Candlesticks`, `Volume`

## 0.0.14
- Added `STOCH` Indicator (Stochastic Oscillator)
- Added `LinePlot`, `AreaPlot` and `BarPlot` primitives

## 0.0.13
- Updated Pypi README

## 0.0.12
- Added `DMI` indicator (`ADX` is now a single series indicator)
- Added `ATRP` indicator (Average True Range Percentage)
- Plotting Logic moved out of indicators
- Experimental `color_scheme` and `Color` modifier

## 0.0.9
- Moved indicator ploting logic to `indicators` module
- Removed deprecated `helper` module
- Added support for minute data labels
- Removed deprecated stylesheet logic
- Added color options to most primitives

## 0.0.8
- Added tasks.py for project management
- Talib wrapper uses talib functions metadata
- Stylesheets are inactive unless specified

## 0.0.7
- Added labels for minor ticks in RSI and ADX

## 0.0.6
- Added ATR and ADX indicators

## 0.0.5
- Multiple asset plots (tentative)
- Fixed Layout is deprecated. Will be removed in the future

## 0.0.4
- Added github workflow
- Setup uses `pyproject.toml` with `hatchling` backend
- Added tests and linting with `noxfile.py`
- Created `samples` sub-package with sample price data
- Removed data files from tests folder
- Removed some links from readme
- Parametrized tests with pytest
- Fixed Volume Colors

## 0.0.3
- Setup uses `pyproject.toml` and `pdm-backend`
- Column names are converted to lower case automatically
- Helper module is deprecated.
- Added `tox` config with sdist packaging

## 0.0.1
- Initial release
