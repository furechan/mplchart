# Change Log

## 0.0.33
- Renamed `ATRP` indicator to `NATR` (Normalized Average True Range), following mintalib convention
- Added `NATR`, `BBP`, `BBW`, `PPO`, `BOP`, `CMF`, `MFI`, `MACDV`, `DMI`, `ADX` to `mplchart.expressions`
- Removed `ALMA` indicator and `calc_alma` from library (preserved in `playground/alma-indicator.ipynb`)
- **Breaking:** `Chart` no longer normalizes column names silently — prices must be normalized before use
- Added `normalize_prices()` to `mplchart.utils`: lowercases columns and promotes `date`/`datetime` to index (pandas)
- Added `check_prices()` to `mplchart.utils`: raises `ValueError` with a helpful message if prices are not normalized

## 0.0.32
- **Breaking:** pandas is no longer a required dependency. Install `mplchart[pandas]` to use the `mplchart.indicators` module, `mplchart[polars]` for `mplchart.expressions`, or both.
- Added `[pandas]` optional extra in `pyproject.toml` (previously only `[polars]` was optional).
- Moved `calc_price` from `library` to `utils` so the `Price` primitive no longer pulls pandas in.
- Split `mapper.slice()` into `slice_pandas` / `slice_polars`; pandas is imported only on the pandas path.
- Split test suite per backend where relevant: `test_primitives_pandas.py`, `test_primitives_polars.py`. Indicator/expression tests stay as `test_indicators.py` (pandas-only by definition) and `test_expressions.py` (polars-only by definition).
- Added `[env.pandas]` and `[env.polars]` isolated tox envs to regression-test single-backend installs.
- Removed `overbought`, `oversold`, `yticks` class attributes from `RSI`, `CCI`, `MFI`, `ADX`, `DMI`. Configure via primitives instead: `RSI() | LinePlot(overbought=70, oversold=30)` and `chart.pane("above", yticks=(30, 50, 70))` or the `Pane(...)` primitive.
- Removed `plot_yticks`, `plot_oversold`, `plot_overbought` from `AutoPlotter` — fill-between band rendering now lives in `LinePlot`.
- `Stripes` / `Markers` `expr=` now accepts a callable (e.g. `expr=lambda s: s < 30`) in addition to string expressions and `pl.Expr`. Callables are the recommended form when the indicator result is a Series, since string expressions require a named-column frame.
- Renamed `utils.dataframe_eval` → `utils.resolve_expr` to reflect that it handles callables, `pl.Expr`, and strings — and accepts a Series as well as a DataFrame.
- `extract_datetime` now accepts `pl.Date` columns directly (no tz op needed); dropped the `pl.Date` → `pl.Datetime` upcast in `samples._load_polars` — user-supplied polars frames with pure-date indexes now work without loader-side conversion.
- `extract_datetime` selects the temporal column by dtype (`pl.Date` or `pl.Datetime`) instead of by the hardcoded name `"datetime"`. Polars frames can now use any column name for their temporal axis (e.g. `"date"`), closing a parity gap with pandas.
- Renamed the `datetime` column to `date` in bundled `daily-prices.csv`, reflecting that it's a pure date (no time component). `hourly-prices.csv` and `minute-prices.csv` keep the `datetime` column. This exercises both column-name conventions across the test suite.
- Added `pandas` / `polars` pytest markers on the per-backend test files. Filter without tox via `pytest -m pandas` or `pytest -m polars`.
- Added `talib` and `mintalib` pytest markers and corresponding integration test files (`test_mintalib_indicators.py`, `test_mintalib_expressions.py`). `mintalib` is now a dev dependency.

## 0.0.28
- Removed `DateIndexFormatter` and `DateIndexLocator`
- Chart objects automatically converts polars dataframes to pandas

## 0.0.27
- Removed `rebase` option and `rebase_data` method
- Chart now accepts `prices` as first argument, instead of the plot method
- Remove SameAxes, NewAxes primitives. No longer neede with plot `target` arguement.
- `DateIndexLocator` and `DateIndexFormatter` have been deprecated, replaced by DTArray clases

## 0.0.26
- Multi source logic will be removed. Merge/rebase data before plotting see rebase-series.ipynb
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
- Added `NATR` indicator (Normalized Average True Range)
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
