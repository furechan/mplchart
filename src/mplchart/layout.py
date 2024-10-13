""" layout classes """

from matplotlib.gridspec import GridSpec


def make_twinx(ax, label="twinx"):
    """
    Creates a twin x axes and configures y axes to the left
    This is contrast to what Axes.tinwx does by default
    """

    ax2 = ax._make_twin_axes(sharex=ax)
    ax.set_zorder(ax2.get_zorder() + 1)

    if label is not None:
        ax2._label = label

    ax2.set_autoscalex_on(ax.get_autoscalex_on())

    ax2.xaxis.set_visible(False)
    ax2.patch.set_visible(False)

    return ax2


class StandardLayout:
    """Grispec Baeed Layout"""

    use_tight_layout = True

    @classmethod
    def init_vplot(cls, figure, *, label="root"):
        """Returns or creates the root axes"""

        if figure.axes:
            return figure.axes[0]

        ax = figure.add_subplot(label=label)

        return ax

    @classmethod
    def add_vplot(cls, figure, *, label=None, height_ratio=1.0, append=True):
        """
        Returns or create new plots vertically respecting height rations
        This version uses add_subplot api
        Requires tight_layout=True!
        """

        main_ax = 1

        if figure.axes:
            sharex = figure.axes[0]
        else:
            sharex = cls.init_vplot(figure)

        gridspec = sharex.get_gridspec()
        nrows, ncols = gridspec.get_geometry()
        height_ratios = gridspec.get_height_ratios() or [1.0]

        if ncols != 1:
            raise ValueError("Number of columns (%d) must be 1!" % ncols)

        if len(figure.axes) <= main_ax:
            ax = figure.add_subplot(gridspec[0, 0], sharex=sharex)
            return ax

        if append:
            height_ratios = [*height_ratios, height_ratio]
            new_pos, pos_inc = nrows, 0
            nrows += 1
        else:
            height_ratios = [height_ratio, *height_ratios]
            new_pos, pos_inc = 0, 1
            nrows += 1

        gridspec = GridSpec(
            nrows, ncols, height_ratios=height_ratios, hspace=0.0, figure=figure
        )

        for i, ax in enumerate(figure.axes):
            if i >= main_ax:
                spec = ax.get_subplotspec()
                spec = gridspec[spec.num1 + pos_inc, 0]
            else:
                spec = gridspec[:, 0]
            ax.set_subplotspec(spec)

        spec = gridspec[new_pos, 0]
        ax = figure.add_subplot(spec, sharex=sharex, label=label)

        return ax


class FixedLayout:
    """Fixed Layout"""

    use_tight_layout = False

    @classmethod
    def init_vplot(cls, figure, *, label="root"):
        """Returns or creates root axes"""

        if figure.axes:
            return figure.axes[0]

        ax = figure.add_axes([0.0, 0.0, 1.0, 1.0], label=label, in_layout=True)

        return ax

    @classmethod
    def add_vplot(cls, figure, *, label=None, height_ratio=1.0, append=True):
        """
        Returns or create new plots vertically respecting height rations
        This version uses add_axes and generates a warning when tight_layout = True!
        Does not allocate space for the Title area!
        """

        main_ax = 1

        if figure.axes:
            sharex = figure.axes[0]
        else:
            sharex = cls.init_vplot(figure)

        if len(figure.axes) <= main_ax:
            ax = figure.add_axes([0.0, 0.0, 1.0, 1.0], sharex=sharex, in_layout=True)
            return ax

        ax = figure.axes[main_ax]
        bb = ax.get_position()
        height = bb.height * height_ratio
        height = height / (1.0 + height)
        hf = 1.0 - height

        if append:
            (
                y0,
                dy,
            ) = (
                0.0,
                height,
            )
        else:
            (
                y0,
                dy,
            ) = (
                1.0 - height,
                0.0,
            )

        grid = []

        for i, ax in enumerate(figure.axes):
            rect = ax.get_position()
            if i >= main_ax:
                rect = [rect.x0, rect.y0 * hf + dy, rect.width, rect.height * hf]
            grid.append(rect)

        for i, ax in enumerate(figure.axes):
            if i >= main_ax:
                rect = grid[i]
                ax.set_position(rect)

        rect = [0.0, y0, 1.0, height]
        ax = figure.add_axes(rect, sharex=sharex, label=label, in_layout=True)

        return ax
