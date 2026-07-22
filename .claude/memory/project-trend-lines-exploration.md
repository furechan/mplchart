---
name: project-trend-lines-exploration
description: Trend-lines playground workstream — walkback notebook is the lead design; conventions and next steps
metadata:
  type: project
---

Trend-line detection exploration (July 2026) lives in `playground/trend-lines-proto.ipynb` — the **walkback design**: a backward incremental-hull walk with a stack of candidate legs and three pluggable heuristics (`stop_continue`, `stop_folding`, `eval_leg`). The window is an output (the walk stops at regime boundaries), and the result contract is (slope, intercept, origin). Includes a `TrendLines` primitive (thin drawing wrapper over the `trend_lines`/`walk_side` driver functions) and a walk-forward replay loop (truncate 50 bars at a time). The engine + primitive are mirrored in `src/mplchart/primitives/trendlines.py` (exported via `mplchart.primitives`, marked EXPERIMENTAL, in both primitive test rosters) — the notebook is the lab and shadows the installed version; sync stabilized changes back to the module. Two earlier notebooks (`trend-lines-linreg`: pinned-pivot fits with pluggable measure × optimizer and composition-level numba; `trend-lines-hull`: batch convex-hull / sad-optimal lines) were superseded by the walkback and deleted on 2026-07-22 — their key results are summarized here and in the proto notebook's notes.

Conventions the user enforced along the way:

- One concept per idea, minimal knobs: swing = extremum within ±span with span bars each side (one parameter governs the whole definition — no separate confirm width; confirmation delay equals swing width, lower span to catch young swings); a single scale function `avg_move` (mean abs one-bar change over the surveyed range — no global ATR, no std variant); zero disables any knob (span=0 walks every bar, max_gap=0 no fold gate, max_legs=0 no budget) — param types stay plain int/float, no Optional; `None` is reserved for hook returns ("no reason to stop"). Defaults live in DEFAULT_* caps constants, single source of truth.
- Bar positions are named `i1, i2` (not `v1, v2`) — "i signifies position".
- Direction is a parameter, not a data transform: `side=SUPPORT/RESISTANCE` constants (values -1/+1, but that's internal — client code uses the names, heuristics receive `side` and real prices; never pass negated prices, so log/percent/level-based measures stay valid).
- Params live in one commented cell before a single chart; chart view derives from walk output; runner-up legs older than the winner stop at their arrival point.

**Why:** the walkback emerged from the user's own A-B-C thought experiment; they want it kept simple and their formulation respected, refined one heuristic at a time.

**How to apply:** for future trend-line work start from `trend-lines-proto.ipynb`. Known next steps: line expiry/break detection (winners currently project past their break — the missing half of the (slope, intercept, origin) contract), touch-count `eval_leg` (the span/(1+gap) scorer is tie-prone and over-rewards span), patience-based `stop_continue`, log-price variant, and an empirical validation harness scoring lines by forward price behavior. Leg-depth facts (AAPL/SPY 10y): final depth ~5-6, peak ~9-12, max 17.
