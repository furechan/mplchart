# Memory Index

- [Examples notebook structure](project-examples-structure.md) — 5 consolidated notebooks; don't add per-indicator files
- [Run pytest after each refactoring](feedback-run-pytest.md) — always run pytest after each fix, not just at the end
- [Optional imports in tests](feedback-optional-imports.md) — use `pytest.importorskip` not try/except+None; put importorskip after normal imports to avoid ruff E402
- [pane() API replaces target= on plot()](project-pane-api.md) — new fluent method for pane selection; all notebooks migrated
- [Polars migration plan](project-polars-migration.md) — rownum+window slice architecture; docs in migration-breakdown.md and migration-inquiry.md
- [New indicator/expression operator API](project-operator-api.md) — `|` for indicators, `@` for expressions→primitives, `.apply()` replaces deprecated `@`; mplchart is testbed
- [Backend architecture (pandas/polars split)](project-backend-architecture.md) — core is backend-agnostic; indicators/library/pandas are pandas-only opt-in; expressions is polars-only opt-in
- [Commit .envrc files](feedback-envrc.md) — `.envrc` is project metadata, not secrets; commit it. Secrets live in separate gitignored files it sources.
