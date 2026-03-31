# Memory Index

- [Run pytest after each refactoring](feedback-run-pytest.md) — always run pytest after each fix, not just at the end
- [Optional imports in tests](feedback-optional-imports.md) — use `pytest.importorskip` not try/except+None; put importorskip after normal imports to avoid ruff E402
