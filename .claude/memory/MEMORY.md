# Memory Index

- [Examples notebook structure](project-examples-structure.md) — 5 consolidated notebooks; don't add per-indicator files
- [Run pytest after each refactoring](feedback-run-pytest.md) — always run pytest after each fix, not just at the end
- [Optional imports in tests](feedback-optional-imports.md) — use `pytest.importorskip` not try/except+None; put importorskip after normal imports to avoid ruff E402
- [No co-author in commits](feedback-no-coauthor.md) — do not add Co-Authored-By trailers to git commit messages
