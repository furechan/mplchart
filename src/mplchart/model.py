""" Primitive Base class """

from abc import ABC, abstractmethod


class Primitive(ABC):
    """ base class for Primitives """

    @abstractmethod
    def plot_handler(self, data, chart, ax=None):
        ...

    def clone(self, **kwargs):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__, **kwargs)
        return result

