"""Tests for the low-level numpy array utilities."""

import numpy as np

from mplchart.arrays import forward_fill


def test_interior_nans_filled():
    values = np.array([1.0, np.nan, np.nan, 0.0, np.nan, 1.0])
    result = forward_fill(values)
    assert result.tolist() == [1.0, 1.0, 1.0, 0.0, 0.0, 1.0]


def test_leading_nans_preserved():
    values = np.array([np.nan, np.nan, 1.0, np.nan])
    result = forward_fill(values)
    assert np.isnan(result[:2]).all()
    assert result[2:].tolist() == [1.0, 1.0]


def test_all_nan():
    result = forward_fill(np.array([np.nan, np.nan]))
    assert np.isnan(result).all()


def test_no_nans_passthrough():
    values = np.array([1.0, 0.0, 1.0])
    assert forward_fill(values).tolist() == values.tolist()


def test_empty():
    assert len(forward_fill(np.array([]))) == 0


def test_input_not_modified():
    values = np.array([1.0, np.nan])
    forward_fill(values)
    assert np.isnan(values[1])
