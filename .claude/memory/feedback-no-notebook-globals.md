---
name: feedback-no-notebook-globals
description: Avoid notebook globals leaking into functions; make implicit call contracts explicit with typed signatures
metadata:
  type: feedback
---

Functions defined in notebooks must not reference notebook-global variables, and implicit call contracts (e.g. hook signatures invoked by an engine) must be made explicit — typed parameters, `Callable` aliases for hook shapes, annotated factory return types.

**Why:** globals leak into code unseen by both the typechecker and the reader ("argh argh argh — this is the problem with notebook global variables"). Even a legitimate parameter like `side` in an untyped hook looked like a possible global leak because nothing declared where it came from.

**How to apply:** when writing notebook functions, pass everything as parameters; declare hook/callback contracts as `Callable[...]` type aliases near the top (see `StopHook`/`EvalLeg` in [[project-trend-lines-exploration]]'s walkback notebook); annotate inner functions so pyright/ty verify the contract. Cell-level scripts may use globals (that's what cells are), but nothing with a `def` should.
