""" rendering wrappers """

from .extalib import talib_function_check, TalibWrapper

wrapper_registry = dict()


def register(name: str):
    """register a wrapper class for given indicator names"""

    def decorator(func):
        wrapper_registry[name] = func
        return func

    return decorator


def indicator_name(indicator):
    """indicator name (uppercase)"""

    if hasattr(indicator, "__name__"):
        name = indicator.__name__
    else:
        name = indicator.__class__.__name__

    return name.upper()


def get_wrapper(indicator):
    """create rendering wrapper for naive indicator"""

    if hasattr(indicator, "plot_result"):
        return None

    if talib_function_check(indicator):
        return TalibWrapper(indicator)

    name = indicator_name(indicator)

    if name in wrapper_registry:
        wrapper = wrapper_registry.get(name)
        return wrapper(indicator)
