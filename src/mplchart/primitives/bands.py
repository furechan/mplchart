"""Bands primitive"""

from ..model.primitive import BindingPrimitive
from ..utils import get_label


class Bands(BindingPrimitive):
    """Band renderer for upper/lower(/middle) multi-output results.

    Renders the band columns as dotted upper/lower lines with a translucent
    fill between, and an optional dashed middle line — the rendering behind
    auto-plotted BBANDS/KELTNER/DONCHIAN.

    Args:
        indicator: indicator, expression, or already-computed frame with the
            band columns.
        upper (str): name of the upper-band column. Defaults to "upperband".
        middle (str): name of the middle-band column, drawn when present.
            Defaults to "middleband".
        lower (str): name of the lower-band column. Defaults to "lowerband".
        label (str): legend label override; derived from the indicator when None.
        legend (bool): include in the legend. Defaults to True.
        color (str): explicit band color; defaults to the ``bands.color``
            setting, else the next line color.

    Examples:
        Bands(BBANDS(20))
        chart.plot(KELTNER(20) @ Bands())
    """

    def __init__(
        self,
        indicator=None,
        *,
        upper: str = "upperband",
        middle: str = "middleband",
        lower: str = "lowerband",
        label: str | None = None,
        legend: bool = True,
        color: str | None = None,
        pane: str | None = None,
    ):
        super().__init__(indicator)
        self.upper = upper
        self.middle = middle
        self.lower = lower
        self.label = label
        self.legend = legend
        self.color = color
        self.pane = pane

    def apply_to_chart(self, chart):
        ax = chart.canvas.get_axes(self.pane)

        data = chart.view.eval(self.required_indicator())
        columns = list(data.columns) if hasattr(data, "columns") else []

        if self.upper not in columns or self.lower not in columns:
            raise ValueError(
                f"Bands expects a multi-output result with "
                f"{self.upper!r}/{self.lower!r} columns, got {columns or 'a single series'}"
            )

        label = self.label if self.label is not None else get_label(self.indicator)
        label = label if self.legend else None
        color = chart.canvas.resolve_color("bands", ax, override=self.color, fallback="line")

        if self.middle in columns:
            xv, mv = chart.view.series_xy(data[self.middle])
            ax.plot(xv, mv, color=color, linestyle="dashed")

        xv, lv, uv = chart.view.series_xy(data[self.lower], data[self.upper])

        ax.plot(xv, lv, color=color, linestyle="dotted")
        ax.plot(xv, uv, color=color, linestyle="dotted")
        ax.fill_between(
            xv, lv, uv, color=color, interpolate=True, alpha=0.2, label=label
        )
