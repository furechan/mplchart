"""Canvas — the presentation plane: figure, styled panes, pane state, colors.

Owns the matplotlib figure, creates styled panes on demand (root draws the
x-grid, panes draw their y-grid), tracks the current pane, and resolves
colors through the color scheme. Never sees a dataframe — numpy arrays and
axes cross the boundary, frames don't.

Standalone draft (canvas-view roadmap phase 2): not yet hooked into Chart,
which still carries its own copies of the styling and pane logic. The
geometry helpers are shared via ``layout``.
"""

import io

import matplotlib as mpl
import matplotlib.pyplot as plt

from collections import Counter

from .colors import closest_color
from .layout import make_twinx, init_vplot, add_vplot
from .utils import extract_prefix


class Canvas:
    """Presentation plane: a figure with styled panes and color resolution.

    Args:
        figsize (tuple, optional): Figure size as ``(width, height)`` in
            inches; used only when creating a new figure. Defaults to
            ``(12, 9)``.
        figure (Figure, optional): Existing matplotlib Figure to adopt.
            The figure is cleared before use.
        title (str, optional): Title displayed above the main pane.
        color_scheme (dict or iterable of pairs, optional): Mapping of color
            role names to color values (e.g. ``colorup``, ``colordn``).

    Creating a Canvas eagerly creates (or adopts) the figure, sets the tight
    layout engine (required by the pane geometry), and installs the styled
    root axes.
    """

    DEFAULT_FIGSIZE = (12, 9)

    def __init__(self, figsize=None, *, figure=None, title=None, color_scheme=()):
        self.color_scheme = dict(color_scheme)
        self.counter = Counter()

        if figure is not None:
            figure.clf()
            self.figure = figure
        else:
            self.figure = plt.figure(figsize=figsize or self.DEFAULT_FIGSIZE)

        self.figure.set_layout_engine("tight")

        ax = init_vplot(self.figure)
        self.config_root_axes(ax)

        if title:
            self.set_title(title)

    def set_title(self, title):
        """Set the title on the root axes (displayed above the main pane)."""
        if title is None:
            return
        self.root_axes().set_title(title)

    def show(self):
        """show the figure"""
        # figure.show() only works if the figure was not created by pyplot!
        plt.show()

    def render(self, format="svg", *, dpi="figure"):
        """Render the figure to bytes in the specified image format.

        Args:
            format (str): Output format, e.g. ``"svg"``, ``"png"``, ``"pdf"``.
                Defaults to ``"svg"``.
            dpi (float or str): Resolution in dots per inch. Pass ``"figure"``
                to use the figure's own DPI setting. Defaults to ``"figure"``.

        Returns:
            bytes: The rendered image as a byte string.
        """
        file = io.BytesIO()
        self.figure.savefig(file, format=format, dpi=dpi)
        return file.getvalue()

    # --- pane styling ---

    @staticmethod
    def config_root_axes(ax):
        """Style the root axes: background layer drawing the x-grid."""
        ax.set_xmargin(0.0)
        ax.set_axisbelow(True)
        ax.patch.set_visible(False)
        ax.xaxis.grid(True, alpha=0.4)
        ax.yaxis.grid(False)
        ax.tick_params(left=False, labelleft=False)

    @staticmethod
    def config_pane_axes(ax):
        """Style a data pane: transparent patch, y-grid, right yticks, no x-ticks."""
        ax.set_xmargin(0.0)
        ax.set_axisbelow(True)
        ax.patch.set_visible(False)  # see through to root axes drawings
        ax.xaxis.grid(False)
        ax.yaxis.grid(True, alpha=0.4)
        ax.yaxis.tick_right()
        ax.tick_params(
            axis="x", which="both", bottom=False, top=False, labelbottom=False
        )

    # --- pane selection / creation ---

    @staticmethod
    def valid_target(target):
        """whether the target name is valid"""
        return target in ("main", "same", "samex", "twinx", "above", "below")

    def root_axes(self):
        """Root (background) axes — always present."""
        if not self.figure.axes:
            ax = init_vplot(self.figure)
            self.config_root_axes(ax)
        return self.figure.axes[0]

    def main_axes(self):
        """Main price axes (first data pane), created if needed."""
        self.root_axes()
        if len(self.figure.axes) > 1:
            return self.figure.axes[1]
        return self.get_axes()

    def get_axes(self, target=None, *, height_ratio=None):
        """Select existing axes or create new axes depending on target.

        Args:
            target: one of "main", "same" ("samex" is an alias), "twinx",
                "above", "below". Defaults to "same" (the current pane).
            height_ratio: relative height of a newly created pane.
        """
        if target is None:
            target = "same"

        if not self.valid_target(target):
            raise ValueError("Invalid target %r" % target)

        figure = self.figure
        self.root_axes()

        # ignore root and twinx axes
        axes = [
            ax for ax in figure.axes
            if getattr(ax, "_label", None) not in ("root", "twinx")
        ]

        if not axes:
            ax = add_vplot(figure=figure)
        else:
            if target == "main":
                return axes[0]

            if target in ("same", "samex"):
                return axes[-1]

            if target == "twinx":
                return make_twinx(axes[-1])

            append = target == "below"

            if not height_ratio:
                height_ratio = 0.2

            ax = add_vplot(figure=figure, height_ratio=height_ratio, append=append)

        self.config_pane_axes(ax)

        return ax

    def add_legends(self):
        """add legends to all axes that have labeled artists"""
        for ax in self.figure.axes:
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                # default to upper left unless the user has explicitly set legend.loc
                loc = mpl.rcParams["legend.loc"]
                if loc == mpl.rcParamsDefault["legend.loc"]:
                    loc = "upper left"
                ax.legend(loc=loc)

    def dump_axes(self):
        """print axes labels and limits (debug helper)"""
        for i, ax in enumerate(self.figure.axes):
            label = getattr(ax, "_label", None) or "none"
            print(i, label, ax.get_xlim(), ax.get_ylim())

    def count_axes(self, include_root=False, include_twins=False):
        """count axes that are neither root or twinx"""
        count = 0
        for ax in self.figure.axes:
            label = getattr(ax, "_label", None)
            if label == "root" and not include_root:
                continue
            if label == "twinx" and not include_twins:
                continue
            count += 1
        return count

    # --- colors ---

    def next_line_color(self, ax):
        """Next line color either text.color or cycled color"""
        handles, _ = ax.get_legend_handles_labels()
        if len(handles):
            return ax._get_lines.get_next_color()
        else:
            return plt.rcParams["text.color"]

    def next_fill_color(self, ax):
        """Next cycled color for fill"""
        return ax._get_patches_for_fill.get_next_color()

    def get_color(self, name, ax=None, *, fallback=None):
        """Lookup color through the color_scheme.

        ``name`` can be a column name, a short id, or a full label — the
        color_scheme is tried on the raw name first, then on the extracted
        prefix (e.g. ``"macd-12-26-9"`` → ``"macd"``).
        """
        color = fallback

        colors = self.color_scheme
        if colors:
            key = name if name in colors else extract_prefix(name)
            if key in colors:
                color = colors[key] or color

        if isinstance(color, list):
            ckey = ax, name
            count = self.counter[ckey]
            self.counter[ckey] += 1
            color = color[count % len(color)] if color else None

        if color and color.startswith("~"):
            color = closest_color(color.removeprefix("~"))

        if color == "line":
            color = self.next_line_color(ax)
        elif color == "fill":
            color = self.next_fill_color(ax)

        return color
