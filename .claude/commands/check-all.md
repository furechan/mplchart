Run the following checks in order. After each one report the result clearly.
If the check passed cleanly, say so and move on automatically.
If there are issues, stop and report them — ask whether to fix, skip, or abort before continuing.

## 1. Lint

```bash
uv run ruff check
```

Report any violations. If there are auto-fixable issues, ask whether to run `ruff check --fix`.

## 2. Type check

```bash
uv run ty check
```

Report any errors. If there are errors, ask whether to investigate before continuing.

## 3. Tests

```bash
uv run pytest -q
```

Report any failures. If tests fail, stop — do not continue to the next checks.

## 4. Indicator parity

```bash
uv run python scripts/compare-indicators.py
```

Report any gaps between indicators and expressions. Ask whether they look intentional or worth addressing.

## 5. Summary

Once all checks are done, give a one-line overall verdict: all clear, or list what needs attention.
