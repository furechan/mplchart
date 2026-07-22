"""TrendLines primitive — walkback trend-line detection.

EXPERIMENTAL: this primitive and its engine are under active development
in ``playground/trend-lines-proto.ipynb`` and are likely to change.
Keep this module in sync with the notebook's engine and primitive cells.

The engine walks the bars backward from the most recent swing,
maintaining a stack of candidate trendline legs — geometrically the
convex hull of the bars walked so far, so every leg is a genuine
two-touch line. Three pluggable heuristics govern the walk: a continue
gate (time / leg budget), a fold gate (reject regime-bridging folds),
and a leg scorer that picks the winner. The lookback window is an
output, not an input: the walk stops at regime boundaries.
"""

import numpy as np

from typing import Callable, NamedTuple, TypedDict

from numpy.lib.stride_tricks import sliding_window_view

from ..model.primitive import Primitive
from ..utils import col_to_numpy


# The two sides. Client code uses the names, never the values — that the
# constants double as the direction multiplier is an implementation
# detail of the geometry below.
SUPPORT = -1
RESISTANCE = +1

# Hook contracts — the walk calls these; the factories below build them.
# A stop hook returns None to proceed or a reason string to stop.
StopHook = Callable[[int, list[int], np.ndarray, int], str | None]  # (i, stack, y, side)
EvalLeg = Callable[[np.ndarray, int, int, int], float]  # (y, i1, i2, side)


class WalkParams(TypedDict, total=False):
    """Typed parameter bundle for walk_side / trend_lines / TrendLines."""

    span: int
    max_gap: float
    max_bars: int
    max_legs: int


# Default walk parameters — the single source of truth; every entry point
# (heuristic factories, walk_side, TrendLines) defaults to these.
# Zero disables a knob (same convention as span=0).
DEFAULT_SPAN: int = 5
DEFAULT_MAX_GAP: float = 6.0
DEFAULT_MAX_BARS: int = 250
DEFAULT_MAX_LEGS: int = 0


def leg_line(y, i1, i2):
    """(slope, intercept) of the line through bars i1 and i2 of y."""
    m = (y[i2] - y[i1]) / (i2 - i1)
    return m, y[i1] - m * i1


def avg_move(y, lo=0):
    """Per-bar scale of y over bars lo..end: the mean absolute one-bar
    change — the close-to-close cousin of the daily trading range.
    Local to the surveyed range, so old structure is measured in its own
    era's units. Built on changes, not levels (level-stdev is inflated
    by trends and regime jumps), and robust to a few outlier bars."""
    d = np.diff(y[lo:])
    return float(np.abs(d).mean()) if len(d) else 1.0


def avg_gap(y, i1, i2, lo, side=RESISTANCE):
    """Average distance between the line through (i1, i2) and y over bars
    lo..end, in units of the range's own average move — oriented so a
    valid line reads positive on either side. The line is linear, so its
    average over the range is its value at the range midpoint — a
    difference of averages."""
    m, b = leg_line(y, i1, i2)
    mid = (lo + len(y) - 1) / 2
    return float(side * (m * mid + b - y[lo:].mean()) / avg_move(y, lo))


def local_extrema(y, span, side=RESISTANCE):
    """Indices of the swings of y: bars that are the extremum within
    +/- span bars, with span real bars on each side. One parameter
    governs the whole definition — a bar near the edges (including the
    last bars) is not a swing until span bars exist beyond it.
    RESISTANCE finds peaks, SUPPORT valleys."""
    z = y * side  # comparisons only — heuristics never see this
    window = 2 * span + 1
    rolling = sliding_window_view(z, window).max(axis=1)
    return np.where(z[span:-span] == rolling)[0] + span


def walkback(y, *, stop_continue: StopHook, stop_folding: StopHook,
             span: int = 0, side: int = RESISTANCE):
    """Backward hull walk over real prices.

    side: RESISTANCE fits a line above the highs, SUPPORT a line below
    the lows. The heuristics always receive the actual prices — the
    side is a parameter, not a data transform.

    span: swing filter width. With span > 0, only swings (local extrema
    within +/- span bars, span bars on each side) are touch points, and
    the walk anchors at the most recent swing instead of the last bar.
    Legs then clear every swing, and brief pokes by non-swing bars are
    tolerated — this kills single-bar staircase legs and wick noise.
    The quality heuristics still measure coverage against all bars.
    span=0 is the degenerate case: every bar is a touch point and the
    walk anchors at the last bar.

    Returns (stack, origin, reason): hull vertex indices newest-first,
    the oldest bar still covered, and the reason the walk ended.
    """
    n = len(y)
    if span > 0:
        points = [int(i) for i in local_extrema(y, span, side)[::-1]]
        anchor = points.pop(0) if points else n - 1
    else:
        points = range(n - 2, -1, -1)
        anchor = n - 1

    stack = [anchor]
    origin = anchor
    for i in points:
        # proposed folds — the new point pokes at or beyond the last leg
        while len(stack) >= 2:
            m, b = leg_line(y, stack[-2], stack[-1])
            if side * (y[i] - (m * i + b)) < 0:
                break
            if reason := stop_folding(i, stack, y, side):
                return stack, origin, reason
            stack.pop()
        if reason := stop_continue(i, stack, y, side):
            return stack, origin, reason
        stack.append(i)
        origin = i
    return stack, origin, "data exhausted"


def make_stop_continue(max_bars: int = DEFAULT_MAX_BARS,
                       max_legs: int = DEFAULT_MAX_LEGS) -> StopHook:
    """Continue gate — point inside the last leg: keep walking?

    Two trivial conditions with different semantics: max_bars bounds
    time (safety net), max_legs bounds structural richness — stop once
    the stack holds enough candidate timescales to choose from. Depth
    is not monotone (folds shrink it), so max_legs alone does not
    guarantee termination; keep max_bars alongside it.
    """
    def stop_continue(i: int, stack: list[int], y: np.ndarray, side: int) -> str | None:
        if max_legs > 0 and len(stack) - 1 >= max_legs:
            return "leg budget"
        if len(y) - 1 - i > max_bars:
            return "max bars"
        return None
    return stop_continue


def make_stop_folding(max_gap: float = DEFAULT_MAX_GAP) -> StopHook:
    """Fold gate — reject a proposed fold when the folded leg
    (stack[-2] -> i) would sit more than max_gap average moves away from
    the tail it must cover. max_gap=0 disables the gate."""
    def stop_folding(i: int, stack: list[int], y: np.ndarray, side: int) -> str | None:
        if max_gap > 0 and avg_gap(y, stack[-2], i, i, side) > max_gap:
            return "fold rejected"
        return None
    return stop_folding


def make_eval_leg() -> EvalLeg:
    """Leg scorer — leg span, discounted by how far the line sits from
    the prices over the stretch it serves (old touch to now)."""
    def eval_leg(y: np.ndarray, i1: int, i2: int, side: int) -> float:
        span = i1 - i2
        gap = avg_gap(y, i1, i2, i2, side)
        return span / (1.0 + gap)
    return eval_leg


def select_leg(stack, y, eval_leg: EvalLeg, side: int = RESISTANCE):
    """Score every leg in the stack, return (legs, scores, winner index)."""
    legs = list(zip(stack, stack[1:]))
    scores = [eval_leg(y, i1, i2, side) for i1, i2 in legs]
    return legs, scores, int(np.argmax(scores))


class WalkResult(NamedTuple):
    """Scored outcome of one walkback side."""

    legs: list[tuple[int, int]]
    scores: list[float]
    gaps: list[float]
    win: int
    origin: int
    reason: str


def walk_side(y, *, side: int = RESISTANCE, span: int = DEFAULT_SPAN,
              max_gap: float = DEFAULT_MAX_GAP,
              max_bars: int = DEFAULT_MAX_BARS,
              max_legs: int = DEFAULT_MAX_LEGS) -> WalkResult:
    """Run one walkback side on real prices and score the legs.

    side=RESISTANCE walks the highs, side=SUPPORT walks the lows.
    """
    stop_continue = make_stop_continue(max_bars=max_bars, max_legs=max_legs)
    stop_folding = make_stop_folding(max_gap=max_gap)
    eval_leg = make_eval_leg()

    stack, origin, reason = walkback(
        y, stop_continue=stop_continue, stop_folding=stop_folding, span=span, side=side
    )
    legs, scores, win = select_leg(stack, y, eval_leg, side)
    gaps = [avg_gap(y, i1, i2, i2, side) for i1, i2 in legs]
    return WalkResult(legs, scores, gaps, win, origin, reason)


def trend_lines(high, low, **params) -> dict[str, WalkResult]:
    """Both sides on raw high/low arrays. Returns {name: WalkResult}.

    params: see WalkParams (span, max_gap, max_bars, max_legs).
    """
    return {
        "support": walk_side(low, side=SUPPORT, **params),
        "resistance": walk_side(high, side=RESISTANCE, **params),
    }


class TrendLines(Primitive):
    """Walkback trendlines: a support and a resistance ladder per chart.

    EXPERIMENTAL: heuristics, parameters, and output are likely to
    change; developed in ``playground/trend-lines-proto.ipynb``.

    Thin drawing wrapper over ``trend_lines`` — run that function on raw
    high/low arrays for debugging. Draws the ladder: the winning leg and
    the runner-ups newer than it extend to now; older legs stop at their
    arrival point. Touch points are marked.

    Args:
        span: swing filter width — only swings (extrema within +/- span
            bars, with span bars on each side) qualify as touch points.
            span=0 degrades to the raw walk: every bar is a touch point,
            anchored at the last bar.
        max_gap: fold-gate horizon knob, in average moves (avg_move over
            the surveyed range). A fold bridging structure further away
            from the tail is rejected and the walk stops at the regime
            boundary. 0 disables the gate.
        max_bars: time safety net for the walk.
        max_legs: leg budget — stop once the stack holds this many legs
            (peak depth runs ~9-12 empirically, 17 max). 0 disables.
        colors: (support, resistance) line colors.
    """

    def __init__(self, span: int = DEFAULT_SPAN, *,
                 max_gap: float = DEFAULT_MAX_GAP,
                 max_bars: int = DEFAULT_MAX_BARS,
                 max_legs: int = DEFAULT_MAX_LEGS,
                 colors: tuple[str, str] = ("green", "red")):
        self.span = span
        self.max_gap = max_gap
        self.max_bars = max_bars
        self.max_legs = max_legs
        self.colors = colors

    def apply_to_chart(self, chart):
        ax = chart.canvas.get_axes()
        prices = chart.view.prices
        high = np.asarray(col_to_numpy(prices, "high"), dtype=float)
        low = np.asarray(col_to_numpy(prices, "low"), dtype=float)

        results = trend_lines(
            high, low, span=self.span, max_gap=self.max_gap,
            max_bars=self.max_bars, max_legs=self.max_legs,
        )

        for (name, result), color in zip(results.items(), self.colors):
            y = low if name == "support" else high
            self._draw_side(chart, ax, y, result, color, name)

    def _draw_side(self, chart, ax, y, result, color, label):
        n = len(y)
        for k, (i1, i2) in enumerate(result.legs):
            m, b = leg_line(y, i1, i2)
            # winner and newer legs extend to now; older stop at arrival
            hi = n if k <= result.win else i1 + 1
            vals = np.full(n, np.nan)
            vals[i2:hi] = m * np.arange(i2, hi) + b
            xs, vv = chart.view.series_xy(vals)
            if k == result.win:
                ax.plot(xs, vv, color=color, linewidth=1.8, label=label)
            else:
                ax.plot(xs, vv, color=color, linewidth=1.0, alpha=0.3)

            marks = np.full(n, np.nan)
            marks[[i1, i2]] = y[[i1, i2]]
            xm, vm = chart.view.series_xy(marks)
            ax.scatter(xm, vm, color=color, s=25, alpha=0.6)
