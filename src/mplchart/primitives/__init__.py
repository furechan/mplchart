"""mplchart drawing primitives.

Primitives are the drawing building blocks passed to ``chart.plot(...)``:
price renderers (``Candlesticks``, ``OHLC``, ``Renko``, ...), generic
renderers that bind an indicator or expression via ``@`` or a positional
argument (``Line``, ``Area``, ``Bars``, ``Bands``), overlays
(``Markers``, ``Stripes``, ``VLine``, ``HLine``), and layout controls
(``Pane``). Plot order matters: primitives land on the current pane, and
``Pane`` creates a new one for the primitives that follow.
"""

from ..model.primitive import Primitive, BindingPrimitive
from .candlesticks import Candlesticks
from .heikinashi import HeikinAshi
from .renko import Renko
from .pointfigure import PointFigure
from .volume import Volume
from .ohlc import OHLC
from .swings import Swings
from .stripes import Stripes
from .markers import Markers
from .autoplot import AutoPlot
from .lineplot import Line, LinePlot
from .areaplot import Area, AreaPlot
from .bands import Bands
from .barplot import Bars, BarPlot
from .zigzag import ZigZag
from .trendlines import TrendLines
from .pane import Pane
from .vline import VLine
from .hline import HLine

__all__ = [
    "AutoPlot",
    "Candlesticks",
    "HeikinAshi",
    "OHLC",
    "Renko",
    "PointFigure",
    "Volume",
    "Line",
    "Area",
    "Bars",
    "Bands",
    "Markers",
    "Stripes",
    "Swings",
    "ZigZag",
    "TrendLines",
    "Pane",
    "VLine",
    "HLine",
    "Primitive",
    "BindingPrimitive",
    # Deprecated compatibility wrappers.
    "LinePlot",
    "AreaPlot",
    "BarPlot",
]
