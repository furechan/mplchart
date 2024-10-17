"""primitive base class"""

import copy

from abc import ABC, abstractmethod


from .utils import short_repr


class Primitive(ABC):
    """Primitive abstract base class"""

    @abstractmethod
    def plot_handler(self, data, chart, ax=None):
        """Plot handler is called before any callculation"""
        ...

    def clone_legacy(self, **kwargs):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__, **kwargs)
        return result

    def clone(self, **kwargs):
        result = copy.copy(self)
        result.__dict__.update(self.__dict__, **kwargs)
        return result


class Wrapper(ABC):
    """Indicator plotting wrapper"""

    @abstractmethod
    def plot_result(self, data, chart, ax=None): ...


class Indicator(ABC):
    """Indicator Base Class"""

    __repr__ = short_repr

    @abstractmethod
    def __call__(self, data): ...

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

