# Memory Index

- [Examples notebook structure](project-examples-structure.md) — 8 consolidated notebooks; don't add per-indicator files
- [Run pytest after each refactoring](feedback-run-pytest.md) — always run pytest after each fix, not just at the end
- [Optional imports in tests](feedback-optional-imports.md) — use `pytest.importorskip` not try/except+None; put importorskip after normal imports to avoid ruff E402
- [pane() API replaces target= on plot()](project-pane-api.md) — new fluent method for pane selection; all notebooks migrated
- [Indicator/expression operator API](project-operator-api.md) — `|` for indicators, `@` for expressions→primitives; ComposedIndicator removed
- [Backend architecture (pandas/polars split)](project-backend-architecture.md) — core is backend-agnostic; indicators/library/pandas are pandas-only opt-in; expressions is polars-only opt-in
- [Commit .envrc files](feedback-envrc.md) — `.envrc` is project metadata, not secrets; commit it. Secrets live in separate gitignored files it sources.
- [VS Code interpreter path warning](feedback-vscode-interpreter-path.md) — if `.venv` exists but VS Code warns on `.venv/bin/python`, set `python.defaultInterpreterPath` to `${workspaceFolder}/.venv/bin/python` in workspace settings.
- [Changelog style](feedback-changelog-style.md) — keep entries terse; no inline rationale
- [Pandas expressions gotchas](project-pandas-expressions-gotchas.md) — `__getattr__` trap, `callable` trap, private `_eval_expression` hook; detection via `type(item).__dict__`
- [Silence type checker with type: ignore, not casts](feedback-silence-pyright.md) — use `# type: ignore[...]` for false positives; don't wrap in runtime casts
