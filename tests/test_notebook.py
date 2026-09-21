"""Notebook widget behavior with backend-native prices and no network calls."""

import subprocess
import sys

import matplotlib.pyplot as plt
import numpy as np
import pytest


@pytest.fixture
def notebook():
    pytest.importorskip('ipywidgets')
    pytest.importorskip('IPython')
    from mplchart import notebook
    return notebook


@pytest.fixture(params=['pandas', 'polars'])
def prices(request):
    pytest.importorskip(request.param)
    from mplchart.samples import sample_prices
    return sample_prices(backend=request.param).tail(100)


@pytest.fixture
def rendered(notebook, monkeypatch):
    figures = []
    monkeypatch.setattr(notebook, 'display', figures.append)
    return figures


def test_controls_redraw_without_refetch(notebook, prices, rendered):
    class Feed:
        def __init__(self):
            self.calls = []

        def get(self, ticker):
            self.calls.append(ticker)
            return prices

    feed = Feed()
    existing = plt.get_fignums()
    widget = notebook.chart_widget(feed.get, ticker='AAPL', max_bars=30, figsize=(8, 5))
    controls, output = widget.children
    ticker, bars = controls.children
    assert controls.layout.justify_content == 'center'
    assert controls.layout.width == '100%'
    assert not ticker.continuous_update and not bars.continuous_update
    assert feed.calls == ['AAPL']
    assert len(rendered) == 1
    assert rendered[-1].axes[1].collections  # default candlesticks
    np.testing.assert_allclose(rendered[-1].get_size_inches(), [8, 5])
    bars.value = 50
    assert feed.calls == ['AAPL']
    assert len(rendered) == 2
    assert rendered[0].axes[1].get_xlim() != rendered[1].axes[1].get_xlim()
    ticker.value = ' MSFT '
    assert feed.calls == ['AAPL', 'MSFT']
    assert len(rendered) == 3
    assert plt.get_fignums() == existing
    widget.close()
    output.close()


def test_custom_plots_use_full_history(notebook, prices, rendered):
    from mplchart.primitives import Line
    from mplchart.utils import detect_backend
    if detect_backend(prices) == 'pandas':
        from mplchart.indicators import SMA
    else:
        from mplchart.expressions import SMA
    widget = notebook.chart_widget(lambda ticker: prices, max_bars=10, indicators=[Line(SMA(20))])
    line = rendered[-1].axes[1].lines[0]
    assert np.isfinite(line.get_ydata()).all()  # visible data has warm-up history
    assert len(line.get_ydata()) == 10
    widget.close()


def test_bad_input_and_loader_errors_recover(notebook, prices, rendered, capsys):
    calls = []

    def load(ticker):
        calls.append(ticker)
        if ticker == 'BAD':
            raise ValueError('Unknown ticker')
        return prices

    widget = notebook.chart_widget(load, ticker='')
    ticker, bars = widget.children[0].children
    assert calls == []
    assert 'Enter a ticker' in capsys.readouterr().out
    ticker.value = 'BAD'
    assert 'Unknown ticker' in capsys.readouterr().out
    ticker.value = 'AAPL'
    assert len(rendered) == 1
    bars.value = 0
    assert 'greater than zero' in capsys.readouterr().out
    assert calls == ['BAD', 'AAPL']
    bars.value = 20
    assert len(rendered) == 2
    assert calls == ['BAD', 'AAPL']
    widget.close()


def test_plot_failure_closes_figure(notebook, prices, rendered, capsys):
    before = plt.get_fignums()
    widget = notebook.chart_widget(lambda ticker: prices, indicators=['missing-column'])
    assert not rendered
    assert 'missing-column' in capsys.readouterr().out
    assert plt.get_fignums() == before
    widget.close()


def test_initial_validation(notebook):
    with pytest.raises(TypeError, match='get_prices must be callable'):
        notebook.chart_widget(None)
    with pytest.raises(ValueError, match='greater than zero'):
        notebook.chart_widget(lambda ticker: None, max_bars=0)


def test_core_import_without_notebook_dependencies():
    code = '''
import importlib.abc
import sys
class BlockNotebook(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'ipywidgets', 'IPython'}:
            raise ModuleNotFoundError(fullname, name=fullname)
sys.meta_path.insert(0, BlockNotebook())
from mplchart.chart import Chart
assert 'mplchart.notebook' not in sys.modules
try:
    from mplchart.notebook import chart_widget
except ImportError as exc:
    assert "mplchart[notebook]" in str(exc)
else:
    raise AssertionError('Expected optional-dependency installation guidance')
'''
    subprocess.run([sys.executable, '-c', code], check=True, capture_output=True, text=True)
