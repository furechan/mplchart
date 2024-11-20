from dataclasses import dataclass

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
    direction: int # 1 for high, -1 for low
    diff: float = 0.0 # price difference between the pivot and the previous pivot
    cross_diff: float = 0.0 # price difference between the pivot and the previous pivot of the same direction

    def deep_copy(self):
        return Pivot(
            point=self.point.copy(),
            direction=self.direction,
            cross_diff=self.cross_diff,
            diff=self.diff
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

    def get_slope(self) -> float:
        if self.p2.index == self.p1.index:
            return 0.0
        return (self.p2.price - self.p1.price) / (self.p2.index - self.p1.index)

    def copy(self):
        return Line(self.p1.copy(), self.p2.copy())
