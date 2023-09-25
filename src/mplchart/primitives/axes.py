""" Pane priomitive """

from ..model import Primitive


class ForceAxes(Primitive):
    """ Primitive to force axis for next indicator """

    indicator = None

    def __init__(self, target='below'):
        if target not in ('samex', 'twinx', 'above', 'below'):
            raise ValueError(f"Invalid target {target!r}")

        self.target = target

    def __ror__(self, indicator):
        if self.indicator is not None:
            raise ValueError("Indicator already defined!")

        return self.clone(indicator=indicator)

    def __rmatmul__(self, indicator):
        if self.indicator is not None:
            raise ValueError("Indicator already defined!")

        return self.clone(indicator=indicator)

    def plot_handler(self, data, chart, ax=None):
        if self.indicator is not None:
            ax = chart.get_axes(self.target)
            chart.plot_indicator(data, self.indicator, ax=ax)
        else:
            chart.force_axes(self.target)


class NewAxes(ForceAxes):
    """ Primitive to force new axis for next indicator """

    def __init__(self, target='below'):
        super().__init__(target)


class SameAxes(ForceAxes):
    """ Primitive to force same axis for next indicator """

    def __init__(self, target='samex'):
        super().__init__(target)
