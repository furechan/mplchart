""" layout classes """



class FixedLayout:
    """Fixed Layout (legacy)"""

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
