---
name: project-view-transforms
description: renko/pnf shipped as transform-binding primitives over Chart.get_view; design in notes/view-transforms.md
metadata:
  type: project
---

Renko and PnF map onto the model as *prices transforms* (domain changes: variable bricks per bar), not indicators — unlike Heikin-Ashi, which is row-aligned and binds to Candlesticks ([[project-backend-architecture]]). Designed and shipped 2026-07-25; full design history in `notes/view-transforms.md`, prototypes in `playground/prototypes/renko-proto.ipynb` / `pnf-proto.ipynb`.

Shipped architecture: `Chart.get_view(transform=None)` — view created lazily at first access and cached, only the first access may pass a transform (later ones raise), `transform` + `raw_dates` raises, date-axis config lives in the creation path, `chart.view` is a property. Primitives bind their own transform as a *bound method* before delegating: `Renko(brick_size=...)` (Candlesticks subclass, `primitives/renko.py`) and `PointFigure(box_size=..., reversal=...)` (`primitives/pointfigure.py`). Contract: the transform-bearing primitive must be plotted first. `wrap_result(dates=...)` + `get_dates` in utils carry non-row-aligned results.

Conventions: windowing counts bricks/columns; renko volume is per-brick (even-split on multi-brick bars, conserved), pnf volume is a per-bar rate (mean bar volume over column lifetime) — deliberately different. Pandas view slicing is positional (2026-07-26, polars as base model — dates are labels not keys); the earlier +1ns renko nudge is removed. Other open items: percentage boxes, high/low-based pnf.
