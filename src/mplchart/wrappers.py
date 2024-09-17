"""rendering wrappers"""

from functools import singledispatch

from .extalib import TalibWrapper


@singledispatch
def get_wrapper(indicator):
    """create rendering wrapper for indicator"""

    if TalibWrapper.check_indicator(indicator):
        return TalibWrapper(indicator)

    return None
