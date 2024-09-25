"""rendering wrappers"""

from .model import Wrapper

from functools import singledispatch

from .extalib import TalibWrapper


@singledispatch
def get_wrapper(indicator):
    """create rendering wrapper for indicator"""

    if isinstance(indicator, Wrapper):
        return indicator

    if hasattr(indicator, "plot_result"):
        return indicator

    if TalibWrapper.check_indicator(indicator):
        return TalibWrapper(indicator)

    return None
