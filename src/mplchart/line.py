from dataclasses import dataclass
import pandas as pd

@dataclass
class Point:
    time: int
    index: int
    price: float

    def copy(self):
        return Point(self.time, self.index, self.price)

@dataclass
class Pivot:
    point: Point
    direction: int
    level: int = 0
    ratio: float = 0.0
    size_ratio: float = 0.0
    bar_ratio: float = 0.0

    def deep_copy(self):
        return Pivot(
            point=self.point.copy(),
            direction=self.direction,
            level=self.level,
            ratio=self.ratio,
            size_ratio=self.size_ratio,
            bar_ratio=self.bar_ratio
        )

class Line:
    def __init__(self, p1: Point, p2: Point, color: str = 'blue', width: int = 1):
        self.p1 = p1
        self.p2 = p2
        self.color = color
        self.width = width

    def get_price(self, index: int) -> float:
        """Calculate price at given index using linear interpolation"""
        if self.p2.index == self.p1.index:
            return self.p1.price
        
        slope = (self.p2.price - self.p1.price) / (self.p2.index - self.p1.index)
        return self.p1.price + slope * (index - self.p1.index)

    def copy(self):
        return Line(self.p1.copy(), self.p2.copy(), self.color, self.width)
