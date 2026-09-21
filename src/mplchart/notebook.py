"""Notebook chart controls. Install with ``pip install 'mplchart[notebook]'``.

This opt-in module requires ipywidgets and IPython. Core chart imports do not load it.
"""

from collections.abc import Callable, Iterable
from typing import Any

import matplotlib.pyplot as plt

try:
    import ipywidgets as widgets
    from IPython.display import display
except ModuleNotFoundError as exc:
    if exc.name not in {"ipywidgets", "IPython"}:
        raise
    raise ImportError("Notebook charts require: pip install 'mplchart[notebook]'") from exc

from .chart import Chart
from .primitives import Candlesticks, Volume

__all__ = ["chart_widget"]


def chart_widget(
    get_prices: Callable[[str], Any],
    *,
    ticker: str = "AAPL",
    max_bars: int = 250,
    indicators: Iterable[Any] | None = None,
    **chart_options: Any,
) -> widgets.VBox:
    """Create a chart with centered ticker and visible-bar controls.

    Return the widget as the last expression in a notebook cell, or pass it to ``display``. Requires a live notebook kernel and an ipywidgets-compatible frontend. Inputs update on submission rather than every keystroke.

    The loader receives only the ticker and returns a pandas or Polars prices DataFrame. Pass a bound method such as ``feed.get`` directly, or use ``functools.partial`` to bind query options such as frequency. No data-provider dependency is required by mplchart.

    The current ticker's prices are retained when ``max_bars`` changes. This control limits the visible chart window, not the fetched history, so indicators can use earlier bars for warm-up. Switching tickers invokes the loader again; caching and refresh policy belong to the loader. Fetch and plotting errors appear in the output area so inputs remain usable.

    Args:
        get_prices: Callable accepting a ticker and returning prices with mplchart's standard OHLCV layout. Use ``normalize=True`` for other supported column layouts.
        ticker: Initial ticker. Defaults to ``"AAPL"``. Surrounding whitespace is stripped before loading; case is preserved.
        max_bars: Positive number of visible bars. Defaults to 250.
        indicators: Complete sequence passed to ``Chart.plot``, including renderers and panes. Defaults to candlesticks and volume. Use pandas indicators with a pandas loader and Polars expressions with a Polars loader.
        **chart_options: Additional ``Chart`` options, such as ``style``, ``figsize``, ``normalize``, or ``yaxis_log``. The title defaults to the ticker.

    Returns:
        VBox: Centered input row followed by the chart output area.

    Raises:
        TypeError: If ``get_prices`` is not callable.
        ValueError: If the initial ``max_bars`` is not positive.

    Examples:
        from mplchart.notebook import chart_widget
        chart_widget(feed.get, ticker="AAPL", max_bars=250)
    """
    if not callable(get_prices):
        raise TypeError("get_prices must be callable; pass feed.get for a bardata Feed")
    if max_bars <= 0:
        raise ValueError("max_bars must be greater than zero")

    plots = tuple(indicators) if indicators is not None else (Candlesticks(), Volume())
    ticker_input = widgets.Text(value=ticker, description="Ticker:", continuous_update=False)
    bars_input = widgets.IntText(value=max_bars, description="Max bars:", continuous_update=False)
    controls = widgets.HBox(
        [ticker_input, bars_input],
        layout=widgets.Layout(width="100%", justify_content="center"),
    )
    loaded_ticker: str | None = None
    prices: Any = None

    def draw(ticker: str, max_bars: int) -> None:
        nonlocal loaded_ticker, prices
        ticker = ticker.strip()
        if not ticker:
            print("Enter a ticker.")
            return
        if max_bars <= 0:
            print("Max bars must be greater than zero.")
            return
        chart = None
        try:
            if ticker != loaded_ticker:
                prices = get_prices(ticker)
                loaded_ticker = ticker
            options = {"title": ticker, **chart_options}
            with plt.ioff():
                chart = Chart(prices, max_bars=max_bars, **options)
                chart.plot(*plots)
                display(chart.figure)
        except Exception as exc:
            print(f"{type(exc).__name__}: {exc}")
        finally:
            if chart is not None:
                plt.close(chart.figure)

    output = widgets.interactive_output(draw, {"ticker": ticker_input, "max_bars": bars_input})
    return widgets.VBox([controls, output], layout=widgets.Layout(width="100%"))
