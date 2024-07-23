""" primitive base class """

from abc import ABC, abstractmethod


class Primitive(ABC):
    """Primitive abstract base class"""

    @abstractmethod
    def plot_handler(self, data, chart, ax=None):
        """Plot handler is called before any calculation"""
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

