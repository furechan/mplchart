# Change Log

## 0.0.41
- MkDocs documentation site scaffold: `mkdocs.yml` + `docs/` source dir (Material theme, mkdocs-jupyter) rendering the example notebooks via symlink; new `docs` dependency group
- Moved internal design notes from `docs/` to `notes/`; `docs/` is now the published site source
- Docs gallery: `docs/gallery.ipynb` notebook rendered from bundled sample data; `inv gallery` re-executes it in place
- New `examples/indicators.ipynb` — indicator mechanics (applying, panes, binding, chaining, `as_expr`, custom indicators); replaces `indicators-pandas.ipynb` in the docs nav
- New `examples/expressions.ipynb` — expression mechanics (factories, `src` composition, boolean conditions, `wrap_expression` custom factories); replaces `expressions-polars.ipynb` in the docs nav
- `sample_prices` now has typed overloads (`backend="pandas"` → `pd.DataFrame`, `backend="polars"` → `pl.DataFrame`) — fixes Pylance `Series[Any] is not callable` on polars usage
- ty config: exclude `playground/` from type checking; removed stale `type: ignore` in `scripts/update-samples.py`
- Removed `examples/indicators-pandas.ipynb` and `examples/expressions-polars.ipynb` — superseded by the mechanics notebooks and the gallery (unique charts harvested: DONCHIAN, DMI, MACDV, BBP/BBW)
- New `examples/primitives.ipynb` — primitive mechanics by role (price/volume renderers, indicator renderers, condition primitives, panes/reference lines, pattern primitives); replaces `primitives-pandas.ipynb` and `primitives-polars.ipynb` (removed)
- Moved `showcase.svg` and `preview.png` from `output/` to `docs/assets/`; README, update scripts, and pypi-readme paths updated
- Removed `output/talib-functions.json` — orphaned ta-lib metadata dump, nothing referenced it
- Removed the pypi-readme generation step: `readme = "README.md"` directly (showcase image now an absolute URL, examples link dropped); deleted `scripts/process-readme.py`, `output/`, the `inv make` task, and the `tomli` dev dependency
- uv config: `default-groups = ["dev", "docs"]` so plain `uv sync` includes the docs tooling
- `inv check` now runs `nbcheck -x examples docs` (nbcheck ≥ 0.0.4) — fails notebooks committed with unexecuted or cleared outputs, guarding the docs site against blank pages
- GitHub Pages deploy workflow (`.github/workflows/docs.yml`): docs-only env, nbcheck guard, `mkdocs build --strict`, deploy via Pages artifact
- New reference page `docs/reference/backends.md` — pandas vs polars backends: what's shared, indicators vs expressions, choosing and mixing
- New article `docs/articles/mplfinance.ipynb` — mplchart vs mplfinance comparison with side-by-side charts; mplfinance added as a dev dependency
- README: added `TrendLines` to the primitives list

## 0.0.40
- New experimental `TrendLines` primitive (`primitives/trendlines.py`) — walkback trend-line detection: backward hull walk with swing filter, fold gate, and leg scoring; developed in `playground/trend-lines-proto.ipynb`, documented in the primitives example notebooks, API likely to change
- New `dateaxis.py` consolidating `locators.py` + `formatters.py` (both removed); added `config_date_axis(ax, dates)` wiring helper
- Mapper is now matplotlib-free — `config_axes` and `_dt_array` removed; the native `dates` attribute feeds `config_date_axis` (which coerces to numpy at its boundary); `Chart.init_prices` wires it when not `raw_dates`
- Renamed mapper → data view: `mapper.py` → `dataview.py`, `DateMapper` → `DataView`, `PandasDateMapper` → `PandasDataView`, `PolarsDateMapper` → `PolarsDataView`, `get_mapper` → `get_view` (removed), `chart.mapper` → `chart.view` (kept as deprecated alias)
- New `canvas.py` — `Canvas` presentation plane (figure, title, styled root/panes, `get_axes` targets, color machinery, `show`/`render`); Chart now composes it: `chart.canvas` + `chart.view`, with Chart keeping only the fluent surface (`plot`, `pane`, `hline`, `vline`, `show`, `render`, `figure`, `title=`) — figure-plane calls go through `chart.canvas.*` (primitives/tests repointed; `count_axes`/`dump_axes`/`add_legends` moved to Canvas; `set_title`/`get_axes`/`get_color`/`root_axes`/`main_axes` removed from Chart; Chart no longer imports matplotlib)
- Primitives now call the view directly (`chart.view.eval/series_xy/slice/map_date`); Chart's data-plane wrappers (`slice`, `series_xy`, `map_date`, `calc_result`) removed
- Removed `chart.prices` and the dead `init_prices` re-entry warning — the view wraps the frame; access via `chart.view.prices` (primitives updated); `calc_result(None)` returns `view.prices`
- Evaluation moved onto the view: each `DataView` subclass implements `eval(item)` in full — column strings, callables, and its native expressions (polars Expr/tuple with struct unnest; pandas Expression hook); view now wraps the prices frame (`view.prices`); `utils.apply_indicator` deprecated; `chart.calc_result` delegates to `view.eval`
- Deprecated `Candlesticks(use_bars=True)` — legacy bar-based renderer; emits `DeprecationWarning`, slated for removal
- Removed deprecated `Chart(bgcolor=...)` parameter (deprecated since 2024) — use matplotlib styles
- Removed `Chart(holidays=...)` parameter — accepted but never implemented; the rownum date mapper eliminates gaps by construction
- Documented `VLine` / `chart.vline()` in the primitives example notebooks; `plot_vline()` retained as a legacy alias
- README: refreshed primitives and indicators lists — dropped removed `Price`, renamed `Peaks` → `Swings` and `MIDPRICE` → `MEDPRICE`, added `Stripes`, `Markers`, `AVGPRICE`

## 0.0.39
- Vectorized `Candlesticks`/`OHLC` vertex construction — verts passed as an `(n, k, 2)` array, hitting `PolyCollection.set_verts` fast path
- Fixed `raw_dates` mode candles/bars misalignment — datetime x-coordinates now convert to matplotlib date numbers via `utils.xvalues_to_float` (previously baked in as microseconds-since-epoch, off-scale vs line plots)
- New `utils.plot_vbars` — vertical bars as a single `PolyCollection`; `Volume`, `BarPlot`, and `AutoPlot` histogram bars now use it instead of per-bar `ax.bar` Rectangles (~17× faster full-chart render at 5000 bars)
- `Stripes` renders all bands as a single `PolyCollection` instead of one `axvspan` patch per region

## 0.0.38
- Renamed example notebooks — dropped the redundant `chart-` prefix (`primitives-pandas`, `primitives-polars`, `expressions-polars`, `indicators-pandas`); renamed `compare-tickers` → `multiple-tickers`; restored the missing `examples/README.md` index that the main README links to
- Renamed `Peaks` → `Swings` — cross-platform swing high/low vocabulary (TradeStation `SwingHigh`/`SwingLow`, NinjaTrader `Swing`); dual-mode behavior unchanged; a dedicated series-study primitive (name TBD) may later take over the bound-indicator mode
- Retired `utils.series_data` and the legacy `utils.series_xy` helper (dead code); `Indicator.get_series` inlines the simplified source selection (named column, default close, series passthrough); `calc_price` moved from `utils` into `library.py` — pandas-stack plumbing now lives entirely in pandas-only modules
- Renamed `MIDPRICE` → `MEDPRICE` (HL/2) in both stacks — adopts talib naming; frees `MIDPRICE` for a possible talib-style rolling midpoint. Added `AVGPRICE` (OHLC/4) to both stacks
- Removed the `Price` primitive — use the string column form (`LinePlot("close")`, `chart.plot("close")`) or the named price indicators (`MEDPRICE`/`TYPPRICE`/`WCLPRICE`/`AVGPRICE`)
- Dropped `item=` from `LinePlot`/`BarPlot`/`AreaPlot` — select a column by composing a single-output expression (`.struct.field(...)` on polars, `as_expr(item=...)` on pandas); multi-output results raise `ValueError`
- A plain string is now a first-class indicator form meaning column reference only — resolved in `apply_indicator` as native column access (`prices[name]`, `pl.col` semantics); `LinePlot("close")`, `chart.plot("close")`, and `"close" @ LinePlot()` all work. Derived prices are indicators (`TYPPRICE()` etc.), not string aliases
- `series_xy` now enforces the full-length contract — a length-mismatched value raises `ValueError` instead of being silently clamped by numpy slicing
- Backend-native mappers: `DateMapper` pure contract, `PandasDateMapper` (join-on-xloc-series) and `PolarsDateMapper` (positional), created from the prices frame via `get_mapper(prices, raw_dates=)`; `raw_dates` is a mode flag, not a class. Legacy `DateIndexMapper`/`RawDateMapper` removed after parity verification (both backends × both modes × window configs); `utils.extract_datetime` removed (date extraction is native per mapper)
- Added `Chart.series_xy` delegating to the mapper; primitives no longer access `chart.mapper` directly
- `Peaks` refactored to two explicit modes decided by the constructor: `indicator=None` → peaks/valleys on prices high/low; bound indicator → peaks and valleys on its series. `item=` removed; `indicator` is now the first positional argument (`Peaks(5)` → `Peaks(span=5)`); multi-output results raise `ValueError`
- Removed `last_result` adjacency chaining — a bare primitive no longer picks up the previous indicator's result; bind explicitly (`Peaks(SMA(50))` or `SMA(50) @ Peaks()`). `calc_result` is now a pure function
- `LinePlot`/`BarPlot`/`AreaPlot`/`Stripes`/`Markers`/`AutoPlot` now require an indicator (`ValueError` otherwise) via `BindingPrimitive.required_indicator`
- `chart.slice` is now only ever called on `chart.prices`
- Removed unused `indicator` parameter from `Chart.get_color`
- Reverted nox back to tox (tox-uv): declarative config fits this repo; same everyday set plus `tox -m full` for the 3.10-3.14 matrix; no PATH shims (tox-uv provisions via the uv store)
- Fixed `closest_color` returning RGB tuples with matplotlib >= 3.11 — result is normalized to hex
- Fixed `RawDateMapper.map_date` not stripping tzinfo — tz-aware dates (e.g. `vline`) landed at the UTC-converted x in `raw_dates` mode
- Removed `lru_cache` from `sample_prices` — callers now get a fresh DataFrame instead of a shared cached instance
- Rewrote polars `WMA` using `rolling_mean(weights=...)` (bearta-style) — now matches talib exactly, yields null for the first `period-1` rows instead of partial sums, and drops a bogus `set_sorted` flag
- `closest_color` now returns the matched color value instead of a `"CN"` reference resolved against the default cycle
- Pandas `calc_bbands`/`calc_bbp`/`calc_bbw` now use close instead of typical price — matches talib and the polars backend
- Polars `EMA` now uses `adjust=False, ignore_nulls=True` — matches the pandas backend (also affects DEMA/TEMA/MACD/PPO/KELTNER)
- Pandas `calc_hma` half-period now `period // 2` — matches the polars backend and bearta
- `ROC` indicator default period changed from 20 to 1 — matches the polars expression; docstring now says fractional (not percentage) change
- Added `tests/test_backend_parity.py` — numeric pandas/polars parity tests for 18 indicator pairs
- Removed legacy logic from `datetimes.py`: shadowed `FREQ_VALUES` dict, dead `step` parse in `date_ticks`, self-mapping `formats` dict in `date_labels`
- Removed unused `calc_pdi`/`calc_ndi` from `library.py`
- Removed always-true guards in `Chart.init_prices` and `DateIndexMapper.config_axes`
- `sample_prices` now validates `freq` against `SAMPLE_FREQUENCIES` with a clear error
- `plot_cspoly`/`plot_csbars` parameters are now required keywords — removed unreachable ax/color re-defaulting (resolution lives in `Candlesticks.apply_to_chart`)
- Deduplicated smoothing internals: `calc_rsi`/`calc_atr`/`calc_dmi` now reuse `calc_rma`/`calc_trange`; polars `DMI` reuses `RMA`
- Docstring fixes: `Chart` prices are documented as required (with `normalize` param); multi-output indicators name their actual columns (`macdsignal`, `slowk`, `upperband`, ...); `BBP` documented as 0-100; `Candlesticks` colors by previous close; `Peaks` documents last-result behavior; assorted typos
- Removed unreachable prices checks in `Chart.plot`/`plot_indicator` (prices are enforced at init)
- Removed `target=` parameter from `Chart.plot` and from `LinePlot`/`AreaPlot`/`BarPlot` — pane selection goes through `pane()` / the `Pane` primitive (see docs/axes-stickiness.md)
- Docs now promote the constructor form `LinePlot(SMA(50), ...)` over the `@` binding operator (README, notebooks, docstrings); `@` remains supported as the operator form
- `AutoPlot` now accepts an indicator as first argument, like the other binding primitives
- Extracted `BaseDateMapper` ABC — `DateIndexMapper`/`RawDateMapper` now share `__init__`, windowing, `series_xy`, `slice`/`slice_polars`, and the tz-strip helper; subclasses keep `rownum`, `slice_pandas`, `map_date`, `config_axes`
- Fixed `STOCH` indicator ignoring its `fastn`/`slown` parameters
- Removed duplicate `slowk`/`slowd` computation in `calc_stoch`
- Fixed minute frequency constant in `datetimes.py` (`1/1400` → `1/1440`)
- Fixed `calc_ppo`/`calc_macd`/`calc_macdv` default `n1` from 20 to the standard 12
- Fixed talib `Function` legend labels showing the full info-dict repr; `get_label` filters pandas Expressions first, so the talib `func_object` check works on the instance again
- Renamed `Primitive.plot_handler(prices, chart, ax=None)` to `apply_to_chart(chart)` — prices are read from `chart.prices`; the `prices` and `ax` parameters are removed (breaking for custom primitives)
- `Chart.calc_result(indicator)` no longer takes a `prices` argument
- Replaced `tox.toml` with `noxfile.py` (nox + uv venv backend); same sessions plus a `full` tag for the Python 3.10-3.14 matrix
- noxfile now sets `UV_PYTHON_INSTALL_BIN=0` so nox's interpreter provisioning (`uv python install`) no longer symlinks `python3.X` executables into `~/.local/bin`; uv-managed pythons stay in uv's store, off PATH

## 0.0.37
- Migrated multi-output polars expressions (`PPO`, `MACD`, `MACDV`, `STOCH`, `DMI`, `BBANDS`, `DONCHIAN`, `KELTNER`) to return a single `pl.struct(...)` Expr instead of a tuple of Exprs
- `apply_indicator` now unnests Struct-typed Series into a multi-column DataFrame; tuple-of-Expr branch retained for interop with external libraries (e.g. mintalib)
- Removed `ExprTuple` from `mplchart.expressions` — no longer needed with struct-Expr returns
- Removed unused `resolve_expr` from `mplchart.utils`

## 0.0.36
- Added `Indicator.as_expr(item=None)` — wraps an indicator as a `pandas.api.typing.Expression` for use with comparison/boolean operators (requires pandas >= 3.0)
- Added `output_names` attribute to multi-output indicators (`DMI`, `PPO`, `MACD`, `MACDV`, `STOCH`, `BBANDS`, `KELTNER`, `DONCHIAN`); required by `as_expr(item=...)` to select a single column
- Updated `Stripes` / `Markers` docstrings and notebook examples to use `as_expr()` instead of lambdas
- Tightened `Indicator.__or__` to require an `Indicator` on the right
- Removed `Indicator.__ror__` and `__pandas_priority__` — apply an indicator with `indicator(prices)` or `prices.pipe(indicator)`
- `IndicatorChain` constructor flattens nested chains
- Split `model.py` into a namespace package: `model/primitive.py` (backend-agnostic) and `model/indicator.py` (pandas-only)

## 0.0.33
- Added `RMA`, `MOM`, `TRANGE`, `MIDPRICE`, `TYPPRICE`, `WCLPRICE` indicators — full parity with `mplchart.expressions`
- Added `calc_mom`, `calc_trange`, `calc_midprice`, `calc_typprice`, `calc_wclprice` to `library.py`
- `expressions.RSI` and `expressions.ATR` now use `RMA` internally instead of inlining `ewm_mean(alpha=1/period)`
- Deleted obsolete migration docs (`docs/migration-proposal.md`, `docs/migration-breakdown.md`, `docs/migration-primitives.md`, `docs/expressions-stopgap.md`)
- `@` is now the unified binding operator for both indicators and expressions; `|` for binding is deprecated
- Legend location defaults to `upper left` unless the user has explicitly set `legend.loc` via rcParams
- Added `docs/architecture.md`; removed architecture content from `CLAUDE.md`
- Removed dead code: `ComposedIndicator`, `Indicator.__matmul__`, `Primitive.clone_legacy`
- Added `BindingPrimitive` base class in `model.py` — owns `indicator`, `__rmatmul__` (`@`), `__ror__` (`|` deprecated); `AutoPlot`, `LinePlot`, `AreaPlot`, `BarPlot`, `Stripes`, `Markers`, `Peaks` all inherit it
- `indicator` is now the first positional arg on all `BindingPrimitive` subclasses: `LinePlot(SMA(50), color="red")` equivalent to `SMA(50) @ LinePlot(color="red")`
- `Stripes` and `Markers` drop `expr` — condition is composed externally before binding
- `Indicator.__or__` added — enables chaining with lambdas: `RSI() | (lambda s: s < 30)`
- Fixed `short_repr` to safely handle non-bool equality results (e.g. polars `Expr == None`)

## 0.0.33
- Renamed `ExprBundle` → `ExprTuple` in `expressions/prelude.py` and re-exported from `mplchart.expressions`
- Removed `SLOPE`, `CURVE`, `TSF`, `QSF`, `RVALUE` indicators (regression family — no vectorized path)
- Added `AutoPlot` primitive — the default plotter is now client-facing, allowing explicit overrides like `SMA(20) @ AutoPlot(label="short_ma")`. When plotting anything that is not already a primitive, the chart wraps it in `AutoPlot()` transparently (same behavior as before).
- Removed internal `AutoPlotter` class and `plotters.py` module — logic folded into `AutoPlot.plot_handler`. Single auto-plot code path.
- `Primitive.__rmatmul__` now accepts tuple-of-Expr bundles (`ExprTuple`), enabling `MACD() @ AutoPlot(...)`.
- Rewrote `RawDateMapper` to implement the same public interface as `DateIndexMapper` (`calc_window`, `series_xy`, `slice`, `slice_polars`, `slice_pandas`, `map_date`, `config_axes`, `rownum`, `datetime_array`). In raw-date mode x-axis coordinates are actual datetime values and matplotlib handles date formatting natively — no custom locator/formatter. `raw_dates=True` now works across primitives (LinePlot, AutoPlot, MACD ExprTuple, …) instead of crashing.
- Removed `Chart.plot_xy` and `Chart.window` side-effect state — the mapper now owns windowing. Callers use `chart.mapper.series_xy(data)` directly; `DateIndexMapper.series_xy(values)` no longer takes a `window` argument (computes it internally).
- `AutoPlot` now uses `chart.mapper.series_xy(series)` directly — same public API as `LinePlot` / `AreaPlot` / `BarPlot` / `Price`. No more reaching into `calc_window()` / `rownum[window]`, and no upfront `chart.slice(data)`.
- Added `xcol=` kwarg to `Chart.slice()` / `mapper.slice()` — when set, the returned frame carries an extra column of that name with per-row x-coordinates (rownum values, or datetimes in `raw_dates` mode). `Candlesticks`, `OHLC`, `Volume`, `ZigZag` now use `chart.slice(prices, xcol="xloc")` instead of computing the window and reaching into `chart.mapper.rownum[window]`. Removes the `hasattr(prices, "index") else prices[window]` backend switch from those primitives.
- `Peaks` now branches on DataFrame vs Series input: DataFrame → `chart.slice(data, xcol="xloc")`, Series → `chart.mapper.series_xy(data)`. No more `calc_window` / `rownum[window]` reach-in. Dropped the redundant `Peaks.process` helper — flow is now linear in `plot_handler` (also fixes a latent bug where a Series input with `item=` set would attempt column lookup and fail).
- `mapper.series_xy` is now variadic — `series_xy(y)` returns `(xs, y)` as before, `series_xy(y1, y2, …)` returns `(xs, y1, y2, …)`. All values share the same window. `Stripes` and `Markers` now use `chart.mapper.series_xy(…)` directly; no more `calc_window` / `rownum` reach-in in either.
- Made `DateIndexMapper.calc_window` / `RawDateMapper.calc_window` private (`_calc_window`). No external callers remain — all primitives use the public `slice` / `series_xy` / `slice(..., xcol=...)` API. Renamed the module-level `_calc_window` helper to `_resolve_window` to avoid name collision.
- Added `label=` kwarg to `LinePlot`, `Stripes`, `Markers` — full parity with `AutoPlot` / `AreaPlot` / `BarPlot`. When `None` (default), behavior is unchanged (`LinePlot` falls back to `get_label(indicator)`; `Stripes` / `Markers` skip the legend entry).
- Removed redundant `chart.window = window` assignments from 6 primitives (`Markers`, `OHLC`, `Peaks`, `Stripes`, `Volume`, `ZigZag`) — the attribute had no remaining readers.
- Reorganized `examples/`: split `chart-primitives.ipynb` into per-backend notebooks (`-pandas`/`-polars`), promoted `chart-render.ipynb` from playground, renamed `rebase-series.ipynb` → `compare-tickers.ipynb`, demoted `custom-indicator.ipynb` to playground
- Added navigation: README `## Examples` table, backend-routing section in `typical-usage.ipynb`, backend note in `chart-indicators.ipynb` / `chart-expressions.ipynb`
- Fixed `examples/chart-expressions.ipynb` RSI cells — `pl.Expr` → primitive uses `@`, not `|` (polars owns `|` as bitwise-or)
- `LinePlot`, `AreaPlot`, `BarPlot`, `Stripes`, `Markers` docstrings now document both `|` (pandas indicator) and `@` (polars expression) forms
- Added `playground/mintalib-indicators.ipynb` and `playground/mintalib-expressions.ipynb` demonstrating mintalib usage with mplchart (exploratory)

## 0.0.32
- Renamed `ATRP` indicator to `NATR` (Normalized Average True Range), following mintalib convention
- Added `NATR`, `BBP`, `BBW`, `PPO`, `BOP`, `CMF`, `MFI`, `MACDV`, `DMI`, `ADX` to `mplchart.expressions`
- Removed `ALMA` indicator and `calc_alma` from library (preserved in `playground/alma-indicator.ipynb`)
- **Breaking:** `Chart` no longer normalizes column names silently — prices must be normalized before use
- Added `normalize_prices()` to `mplchart.utils`: lowercases columns and promotes `date`/`datetime` to index (pandas)
- Added `check_prices()` to `mplchart.utils`: raises `ValueError` with a helpful message if prices are not normalized
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
