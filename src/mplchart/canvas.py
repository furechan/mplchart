"""Canvas — the presentation plane: figure, styled panes, pane state, colors.

Owns the matplotlib figure, creates styled panes on demand (root draws the
x-grid, panes draw their y-grid), tracks the current pane, and resolves
colors through its styler. Never sees a dataframe — numpy arrays and
axes cross the boundary, frames don't.
"""

import io

import matplotlib as mpl
import matplotlib.pyplot as plt

from .layout import make_twinx, init_vplot, add_vplot
from .styles import get_styler


class Canvas:
    """Presentation plane: a figure with styled panes and color resolution.

    Args:
        figsize (tuple, optional): Figure size as ``(width, height)`` in
            inches; used only when creating a new figure. Defaults to
            ``(12, 9)``.
        figure (Figure, optional): Existing matplotlib Figure to adopt.
            The figure is cleared before use.
        title (str, optional): Title displayed above the main pane.
        style (optional): Style spec, normalized via ``get_styler`` — a
            shipped style name (see ``styles.available_styles()``), a spec
            mapping (``stylesheet``/``rc``/``settings``), a ``Style``, or
            a prebuilt ``Styler``.

    Creating a Canvas eagerly creates (or adopts) the figure, sets the tight
    layout engine (required by the pane geometry), and installs the styled
    root axes.
    """

    DEFAULT_FIGSIZE = (12, 9)

    def __init__(self, figsize=None, *, figure=None, title=None, style=None):
        self.styler = get_styler(style)

        with self.styler.context():
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
        with self.styler.context():
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
        with self.styler.context():
            self.figure.savefig(file, format=format, dpi=dpi)
        return file.getvalue()

    # --- pane styling ---

    @staticmethod
    def grid_enabled(axis):
        """Whether the effective rc enables the grid for ``axis`` ("x"/"y").

        Reads ``axes.grid`` and ``axes.grid.axis`` — called inside the
        styler's rc context, so styles control the grid (the mplchart
        default look rides in ``styles.DEFAULT_RC``).
        """
        return mpl.rcParams["axes.grid"] and mpl.rcParams["axes.grid.axis"] in (axis, "both")

    @classmethod
    def config_root_axes(cls, ax):
        """Style the root axes: background layer drawing the x-grid."""
        ax.set_xmargin(0.0)
        ax.set_axisbelow(True)
        ax.patch.set_visible(False)
        ax.xaxis.grid(cls.grid_enabled("x"))
        ax.yaxis.grid(False)
        ax.tick_params(left=False, labelleft=False)

    @classmethod
    def config_pane_axes(cls, ax):
        """Style a data pane: transparent patch, y-grid, right yticks, no x-ticks."""
        ax.set_xmargin(0.0)
        ax.set_axisbelow(True)
        ax.patch.set_visible(False)  # see through to root axes drawings
        ax.xaxis.grid(False)
        ax.yaxis.grid(cls.grid_enabled("y"))
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
            with self.styler.context():
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

        with self.styler.context():
            return self._get_axes(target, height_ratio=height_ratio)

    def _get_axes(self, target, *, height_ratio=None):
        """``get_axes`` body — runs inside the styler's rc context."""
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
        with self.styler.context():
            self._add_legends()

    def _add_legends(self):
        """``add_legends`` body — runs inside the styler's rc context."""
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

    def get_setting(self, role, facet, *, override=None, fallback=None):
        """Lookup a style setting through the styler — see ``Styler.get_setting``."""
        return self.styler.get_setting(role, facet, override=override, fallback=fallback)

    def resolve_color(self, role, ax=None, *, override=None, fallback=None):
        """Resolve a role color through the styler — see ``Styler.resolve_color``."""
        return self.styler.resolve_color(role, ax, override=override, fallback=fallback)
