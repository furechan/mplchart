from dataclasses import dataclass

@dataclass
class BaseDataClass:
    def get(self, attr, default=None):
        return getattr(self, attr, default)

@dataclass
class ChartPoint(BaseDataClass):
    """Defines a point you make on your chart

    `datetime` where on the graph you want to add the point

    If `arrow` will show an arrow pointing to the label
    `arrowprops` should be dict of {"facecolor":"", "arrowstyle":"->"}
    For more options, go to
    https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.annotate.html
    """
    price: float
    datetime: str = None
    label: str = None
    label_offset: int = 1
    color: str = "green"
    arrow: bool = False
    arrowprops: dict = None

__all__ = [k for k in dir() if k != "BaseDataClass"]