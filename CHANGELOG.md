# Change Log

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

## 0.0.2
- Minor update

## 0.0.1
- Initial release
