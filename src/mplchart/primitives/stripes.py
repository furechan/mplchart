"""Stripes primitive"""

import numpy as np

from matplotlib.collections import PolyCollection

from ..model.primitive import BindingPrimitive
from ..utils import xvalues_to_float


class Stripes(BindingPrimitive):
    """Stripes primitive.

    Shades vertical bands across all chart panes during periods when a
    condition is active. Bind a condition indicator via ``@`` or as the
    first positional argument.

    Args:
        indicator: indicator or expression returning a boolean/numeric signal.
            Positive values shade the band; zero or negative do not.
            Can also be bound via ``@``.
        label (str, optional): Legend label. Omit to skip the legend entry.
        color (str, optional): Fill color for the shaded regions.
        alpha (float, optional): Opacity of the shaded regions, between 0.0
            and 1.0.

    Examples:
        Stripes(MACD().as_expr("macdhist") > 0, color="green", alpha=0.15)
    """

    def __init__(self, indicator=None, *, label: str | None = None, color=None, alpha=None):
        super().__init__(indicator)
        self.label = label
        self.color = color
        self.alpha = alpha

    def apply_to_chart(self, chart):
        ax = chart.canvas.root_axes()

        result = chart.view.eval(self.required_indicator())

        xs, values = chart.view.series_xy(result)

        if not len(values):
            return

        # clip to 0/1 and forward-fill NaNs
        flag = np.clip(np.sign(values.astype(float)), 0.0, 1.0)
        nan_mask = np.isnan(flag)
        if nan_mask.any():
            idx = np.where(~nan_mask, np.arange(len(flag)), 0)
            np.maximum.accumulate(idx, out=idx)
            flag = flag[idx]

        # find contiguous on-regions via diff
        padded = np.concatenate([[0.0], flag, [0.0]])
        diff = np.diff(padded)
        starts = np.where(diff > 0)[0]
        ends = np.where(diff < 0)[0]

        if not len(starts):
            return

        xs = xvalues_to_float(xs)
        x0 = xs[starts]
        x1 = xs[ends - 1]

        # one PolyCollection of full-height bands — x in data coords, y in axes
        # fraction via the same blended transform axvspan uses
        kx = np.stack([x0, x0, x1, x1], axis=1)
        ky = np.broadcast_to([0.0, 1.0, 1.0, 0.0], kx.shape)
        verts = np.stack([kx, ky], axis=2)

        poly = PolyCollection(
            verts,  # ty: ignore[invalid-argument-type]  # pyright: ignore[reportArgumentType]  # stubs say Sequence[ArrayLike]; 3-D ndarray is supported
            facecolors=self.color, edgecolors="none", alpha=self.alpha,
            label=self.label, transform=ax.get_xaxis_transform(which="grid"),
        )
        ax.add_collection(poly, autolim=False)
        ax.update_datalim([(x0.min(), 0), (x1.max(), 0)], updatey=False)
        ax.autoscale_view()
