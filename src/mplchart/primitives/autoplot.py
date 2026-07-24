"""AutoPlot primitive — default auto-plotting via dispatch to the renderers"""

from ..model.primitive import BindingPrimitive
from ..utils import get_label

from .bands import Bands
from .barplot import BarPlot
from .lineplot import LinePlot


class AutoPlot(BindingPrimitive):
    """Default plotter primitive.

    Auto-plots an expression or indicator by dispatching each output to a
    renderer primitive: band results (``upperband``/``lowerband``) go to
    ``Bands`` wholesale; otherwise ``*hist`` columns go to ``BarPlot`` and
    everything else to ``LinePlot``, column by column. Styling lives in the
    renderers (keyed by series name). Used implicitly when plotting anything
    that is not already a ``Primitive``; can also be applied explicitly to
    override the legend label.

    Args:
        indicator: indicator or expression to plot. Can also be bound via ``@``.
        label (str): override the legend label. When ``None``, the label is
            derived from the expression/indicator via ``get_label``.

    Examples:
        chart.plot(SMA(20))                                # implicit AutoPlot
        chart.plot(AutoPlot(SMA(20), label="short_ma"))    # explicit override
        chart.plot(MACD() @ AutoPlot(label="macd"))        # operator form
    """

    def __init__(self, indicator=None, *, label: str | None = None):
        super().__init__(indicator)
        self.label = label

    def apply_to_chart(self, chart):
        data = chart.view.eval(self.required_indicator())

        label = self.label if self.label is not None else get_label(self.indicator)
        columns = list(data.columns) if hasattr(data, "columns") else []

        if not columns:
            LinePlot(data, label=label).apply_to_chart(chart)
            return

        if "upperband" in columns and "lowerband" in columns:
            Bands(data, label=label).apply_to_chart(chart)
            return

        counter = 0

        for item in columns:
            first = counter == 0

            if item.endswith("hist"):
                BarPlot(data[item], label=label if first else None, legend=first,
                        alpha=0.5, width=0.8).apply_to_chart(chart)
                continue

            LinePlot(data[item], label=label if first else None, legend=first).apply_to_chart(chart)
            counter += 1
