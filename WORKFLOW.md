# Workflow

## Setup

```bash
uv sync
```

## Development

```bash
uv run pytest        # run tests
uv run ruff check    # lint
uv run ty check      # type check
```

## Invoke tasks

```bash
inv info             # show installed package version
inv check            # lint (ruff) + check example notebooks
inv make             # regenerate README from scripts/process-readme.py
inv build            # clean → update README → build wheel
inv dump             # list contents of built wheel
inv publish          # upload dist/*.whl to PyPI via twine
inv publish --testpypi  # upload to TestPyPI instead
inv bump             # bump patch version in pyproject.toml
inv depcheck         # upgrade packages flagged by Dependabot alerts, then sync
```

## Publishing workflow

Order matters — `bump` runs *after* publishing:

```bash
inv check
inv build
inv publish
inv bump
git add pyproject.toml && git commit -m "Bump version"
```

## Security updates

Run `inv depcheck` to fetch open Dependabot alerts, upgrade the flagged packages
in `uv.lock`, and sync the environment. Review the changes, then commit `uv.lock`.

```bash
inv depcheck
git add uv.lock && git commit -m "Update dependencies to address security alerts"
```
