"""low-level numpy array utilities for mplchart"""

import numpy as np


def forward_fill(values: np.ndarray) -> np.ndarray:
    """Forward-fill NaNs with the last valid value.

    Each NaN inherits the most recent non-NaN value before it; leading NaNs
    (no prior valid value) are left as NaN. Returns a new array — the input
    is not modified.
    """
    values = np.asarray(values, dtype=float)
    mask = np.isnan(values)
    if not mask.any():
        return values

    # index of the most recent valid observation: valid positions keep their
    # own index, NaN positions take 0, and a running maximum propagates the
    # last valid index forward
    idx = np.where(~mask, np.arange(len(values)), 0)
    np.maximum.accumulate(idx, out=idx)
    return values[idx]
