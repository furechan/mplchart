---
name: feedback-notebookedit-celltype
description: NotebookEdit cell_type conversion (code→markdown) leaves stale execution_count/outputs fields — invalid nbformat schema; strip them and re-validate
metadata:
  type: feedback
---

Converting a cell's type with NotebookEdit (`cell_type: markdown` on a code cell) changes `cell_type` but leaves the code-cell-only fields (`execution_count`, `outputs`) in place — markdown cells with those fields violate the nbformat schema. ty fails with "unknown field `execution_count`" and nbcheck fails on the notebook.

**Why:** NotebookEdit replaces source/type but does not reshape the cell dict.

**How to apply:** after any cell-type conversion, strip `execution_count`/`outputs` from the converted cell (json load → del fields → `nbformat.validate` → `nbformat.write`), then run the usual notebook checks. Also: replacing a code cell's source with NotebookEdit clears its outputs — plan to re-execute the notebook (`jupyter nbconvert --execute --inplace`) before nbcheck -x.
