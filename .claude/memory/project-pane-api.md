---
name: pane() API added to Chart
description: Chart gained a pane() method for fluent pane selection, replacing target= parameter on plot()
type: project
---

`Chart.pane(target, *, height_ratio=None)` was added to `chart.py` as the preferred way to select/create panes in the fluent chain. It creates the pane and sets `force_target = "same"` so subsequent `plot()` calls land in it.

New style:
```python
chart.plot(Candlesticks(), SMA(50)).pane("above").plot(RSI()).pane("below").plot(MACD())
```

Old style (deprecated, still works):
```python
chart.plot(RSI(), target="above").plot(MACD(), target="below")
```

`plot()` default `target` was changed to `None` (let indicators choose). All notebooks in `examples/` and `playground/` have been migrated to the new style.

**Why:** `target=` was implicit and only applied to the first indicator per call. `pane()` makes intent explicit and reads naturally in a chain.
