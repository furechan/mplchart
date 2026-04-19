---
paths:
  - "**/*.ipynb"
---

<!-- verification: NBMAKE-K7V2 — remove after testing path-scoped loading -->

After modifying any `.ipynb` file, validate it with both:

```bash
uv run ty check <notebook.ipynb>
uv run pytest --nbmake <notebook.ipynb>
```

For bulk edits, point both at the folder: `uv run ty check examples/` and `uv run pytest --nbmake examples/`.

`nbcheck` alone is insufficient — it validates JSON structure only, not code or execution. `ty check` catches syntax and type errors (including the one-char-per-line shatter that happens when scripted JSON edits iterate a string `source` field). `pytest --nbmake` actually executes the notebook and catches runtime errors (e.g. `pl.Expr | Primitive` which is valid Python but fails at runtime).

Both tools are dev dependencies of this project; no extra setup needed.

When cell IDs are present, prefer `NotebookEdit` over scripted JSON patches — it's representation-agnostic and won't shatter cells.
