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

Always pass the exact notebook path(s) you edited. For bulk edits, pass an explicit list of files — not a directory.

**Never run `pytest --nbmake <folder>/` unless you know every `.ipynb` under it is a pure-assertion test.** Notebooks in `prototypes/`, `examples/`, `extras/`, and similar folders frequently have side effects — network calls, long-running jobs, or writes to repo files. `--nbmake` will execute them all indiscriminately and can corrupt the working tree.

`nbcheck` alone is insufficient — it validates JSON structure only, not code or execution. `ty check` catches syntax and type errors (including the one-char-per-line shatter that happens when scripted JSON edits iterate a string `source` field). `pytest --nbmake` actually executes the notebook and catches runtime errors (e.g. `pl.Expr | Primitive` which is valid Python but fails at runtime).

Both tools are dev dependencies of this project; no extra setup needed.

When cell IDs are present, prefer `NotebookEdit` over scripted JSON patches — it's representation-agnostic and won't shatter cells.
