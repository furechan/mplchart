""" primitive base class """

from abc import ABC, abstractmethod


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
