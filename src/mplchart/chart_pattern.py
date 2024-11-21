from dataclasses import dataclass
from typing import List, Tuple
from abc import abstractmethod
from .line import Pivot
from .zigzag import Zigzag
import numpy as np

import logging
logger = logging.getLogger(__name__)

@dataclass
class ChartPatternProperties:
    offset: int = 0
    min_periods_lapsed: int = 21
    max_live_patterns: int = 50
    avoid_overlap: bool = True # whether to avoid overlapping patterns
    allowed_patterns: List[bool] = None
    allowed_last_pivot_directions: List[int] = None

class ChartPattern:
    """Base class for chart patterns"""
    pivots: List[Pivot]
    pattern_type: int = 0
    pattern_name: str = ""

    @abstractmethod
    def get_pattern_name_by_id(self, pattern_type: int) -> str:
        """Get pattern name from pattern type ID

        Args:
            pattern_type: Pattern type identifier

        Returns:
            str: Name of the pattern
        """
        pass

    def process_pattern(self, properties: ChartPatternProperties,
                       patterns: List['ChartPattern']) -> bool:
        """
        Process a new pattern: validate it, check if it's allowed, and manage pattern list

        Args:
            properties: Scan properties
            patterns: List of existing patterns
            max_live_patterns: Maximum number of patterns to keep

        Returns:
            bool: True if pattern was successfully processed and added
        """
        # Log warning if invalid pattern type detected
        if self.pattern_type == 0:
            return False

        # Get last direction from the last pivot
        last_dir = self.pivots[-1].direction

        # Get allowed last pivot direction for this pattern type
        allowed_last_pivot_direction = 0
        if properties.allowed_last_pivot_directions is not None:
            if self.pattern_type < len(properties.allowed_last_pivot_directions):
                allowed_last_pivot_direction = properties.allowed_last_pivot_directions[self.pattern_type]

        # Check if pattern type is allowed
        pattern_allowed = True
        if properties.allowed_patterns is not None:
            if self.pattern_type > len(properties.allowed_patterns):
                pattern_allowed = False
            else:
                pattern_allowed = (self.pattern_type > 0 and
                                properties.allowed_patterns[self.pattern_type-1])

        # Check if direction is allowed
        direction_allowed = (allowed_last_pivot_direction == 0 or
                           allowed_last_pivot_direction == last_dir)

        if pattern_allowed and direction_allowed:
            # Check for existing pattern with same pivots
            existing_pattern = False
            replacing_patterns = []

            for idx, existing in enumerate(patterns):
                # Check if pivots match
                existing_indexes = set([p.point.index for p in existing.pivots])
                self_indexes = set([p.point.index for p in self.pivots])
                # check if the indexes of self.pivots are a subset of existing.pivots
                if self_indexes == existing_indexes:
                    existing_pattern = True
                    break
                elif self_indexes.issubset(existing_indexes) and properties.avoid_overlap:
                    existing_pattern = True
                    break
                elif existing_indexes.issubset(self_indexes) and properties.avoid_overlap:
                    replacing_patterns.append(idx)

            if not existing_pattern:
                for idx in replacing_patterns:
                    patterns.pop(idx)

                # Set pattern name
                self.pattern_name = self.get_pattern_name_by_id(self.pattern_type)

                # Add new pattern and manage list size
                patterns.append(self)
                while len(patterns) > properties.max_live_patterns:
                    patterns.pop(0)

                return True

        return False

def get_pivots_from_zigzag(zigzag: Zigzag, pivots: List[Pivot], offset: int, min_pivots: int) -> int:
    for i in range(min_pivots):
        pivot = zigzag.get_pivot(i + offset)
        if pivot is None:
            return i
        pivots.insert(0, pivot.deep_copy())
    return i+1

def is_same_height(pivot1: Pivot, pivot2: Pivot, ref_pivots: List[Pivot], flat_ratio: float) -> bool:
    # check if two pivots are approximately flat with a list of reference pivots
    # use the first and last pivots in the list as reference points
    if np.sign(pivot1.direction) != np.sign(pivot2.direction):
        raise ValueError("Pivots must have the same direction")

    # use the reference pivots to calculate the height ratio
    if pivot1.direction > 0:
        ref_prices = min(ref_pivots[0].point.price, ref_pivots[-1].point.price)
    else:
        ref_prices = max(ref_pivots[0].point.price, ref_pivots[-1].point.price)
    diff1 = pivot1.point.price - ref_prices
    diff2 = pivot2.point.price - ref_prices
    ratio = diff1 / diff2
    fit_pct = 1 - flat_ratio
    if ratio < 1:
        same_height = ratio >= fit_pct
    else:
        same_height = ratio <= 1 / fit_pct
    if same_height:
        logger.debug(f"pivot {pivot1.point.index}: {pivot1.point.price:.4f}, "
                     f"pivot {pivot2.point.index}: {pivot2.point.price:.4f} "
                     f"are approximately the same height, "
                     f"ref_prices: {ref_prices:.4f}, ratio: {ratio:.4f}")
    return same_height

