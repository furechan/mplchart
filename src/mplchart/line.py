from dataclasses import dataclass

@dataclass
class Point:
    time: int
    index: int
    price: float
    norm_price: float

    def copy(self):
        return Point(self.time, self.index, self.price, self.norm_price)

@dataclass
class Pivot:
    point: Point
    direction: int
    level: int = 0
    ratio: float = 0.0

    def deep_copy(self):
        return Pivot(
            point=self.point.copy(),
            direction=self.direction,
            level=self.level,
            ratio=self.ratio
        )

class Line:
    def __init__(self, p1: Point, p2: Point):
        self.p1 = p1
        self.p2 = p2

    def get_price(self, index: int) -> float:
        """Calculate price at given index using linear interpolation"""
        if self.p2.index == self.p1.index:
            return self.p1.price
        
        slope = (self.p2.price - self.p1.price) / (self.p2.index - self.p1.index)
        return self.p1.price + slope * (index - self.p1.index)
 
    def get_norm_price(self, index: int) -> float:
        """Calculate normalized price at given index using linear interpolation"""
        if self.p2.index == self.p1.index:
            return self.p1.norm_price
     
        slope = (self.p2.norm_price - self.p1.norm_price) / (self.p2.index - self.p1.index)
        return self.p1.norm_price + slope * (index - self.p1.index) / self.p1.norm_price

    def copy(self):
        return Line(self.p1.copy(), self.p2.copy())
