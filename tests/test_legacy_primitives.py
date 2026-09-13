"""Compatibility of the renamed rendering primitives."""

import inspect

import pytest

from mplchart.primitives import Line, Area, Bars, LinePlot, AreaPlot, BarPlot
from mplchart.primitives.lineplot import LinePlot as ModuleLinePlot
from mplchart.primitives.areaplot import AreaPlot as ModuleAreaPlot
from mplchart.primitives.barplot import BarPlot as ModuleBarPlot


@pytest.mark.parametrize("canonical,legacy,module_legacy", [
    (Line, LinePlot, ModuleLinePlot),
    (Area, AreaPlot, ModuleAreaPlot),
    (Bars, BarPlot, ModuleBarPlot),
])
def test_legacy_constructor_and_binding(canonical, legacy, module_legacy):
    assert legacy is module_legacy
    assert legacy.__init__ is canonical.__init__
    assert inspect.signature(legacy.__init__) == inspect.signature(canonical.__init__)

    with pytest.warns(DeprecationWarning, match=f"{legacy.__name__} is deprecated; use {canonical.__name__}"):
        primitive = legacy("close", color="red")
    assert isinstance(primitive, canonical)
    assert repr(primitive) == repr(canonical("close", color="red")).replace(
        canonical.__name__, legacy.__name__, 1
    )

    # Binding clones via copy.copy, which also invokes the legacy __new__.
    with pytest.warns(DeprecationWarning, match=f"use {canonical.__name__}"):
        bound = "open" @ primitive
    assert isinstance(bound, legacy)
    assert bound.indicator == "open"
    assert bound.color == "red"
    assert primitive.indicator == "close"
