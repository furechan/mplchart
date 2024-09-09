""" primitive base class """

from abc import ABC, abstractmethod

from .utils import short_repr


class Primitive(ABC):
    """Primitive abstract base class"""

    @abstractmethod
    def plot_handler(self, data, chart, ax=None):
        """Plot handler is called before any callculation"""
        ...

    def clone(self, **kwargs):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__, **kwargs)
        return result


class Wrapper(ABC):
    """Indicator plotting wrapper"""

    def __init__(self, indicator):
        self.indicator = indicator

    def __repr__(self, *args, **kwargs):
        return getattr(self.indicator, "__name__", repr(self.indicator))

    def check_result(self, data):
        return True

    @abstractmethod
    def plot_result(self, data, chart, ax=None):
        ...


class Indicator(ABC):
    """Indicator Base Class"""

    __repr__ = short_repr

    @abstractmethod
    def __call__(self, data):
        ...

    def __matmul__(self, other):
        if callable(other):
            return ComposedIndicator(self, other)
        return self(other)



class ComposedIndicator(Indicator):
    """Composed Indicator"""

    def __init__(self, *args):
        if not all(callable(arg) for arg in args):
            raise TypeError("Arguments must be callable")
        self.args = args

    def __repr__(self):
        return " @ ".join(repr(fn) for fn in self.args)

    def __call__(self, data):
        result = data
        for fn in reversed(self.args):
            result = fn(result)
        return result

    def __matmul__(self, other):
        if callable(other):
            return self.__class__(*self.args, other)
        return self(other)

    @property
    def same_scale(self):
        return all(getattr(i, "same_scale", False) for i in self.args)

