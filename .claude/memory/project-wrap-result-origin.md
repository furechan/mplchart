---
name: project-wrap-result-origin
description: wrap_result util is ported from mintalib — the original pandas+polars-compatible indicator design
metadata:
  type: project
---

`wrap_result(result, source)` in `src/mplchart/utils.py` is a port of mintalib's `_wrap_result` (`~/Projects/mintalib/src/mintalib/model/function.py`; earlier prototype in `~/Projects/mintalib/playground/cython-proto.ipynb`). Per the user, this is the original design for backend-compatible indicators: compute in numpy, then wrap the result (array, or dict/namedtuple of arrays) back into the source frame's backend — pandas keeps the source index, polars converts NaN to null, and backend modules are fetched from `sys.modules`, never imported. First consumer: `calc_heikin_ashi` in `primitives/heikinashi.py` ([[project-backend-architecture]]).
