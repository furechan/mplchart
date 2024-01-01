""" Talib extensions """


def talib_function_check(indicator):
    return hasattr(indicator, "func_object")


def talib_function_name(indicator):
    return indicator.info.get("name")


def talib_function_repr(indicator):
    name = indicator.info.get("name")
    params = [repr(v) for v in indicator.parameters.values()]
    return name + "(" + ", ".join(params) + ")"


def talib_same_scale(indicator):
    same_scale_flag = "Output scale same as input"
    flags = indicator.function_flags
    if flags and same_scale_flag in flags:
        return True
