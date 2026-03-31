# mplchart

Python project managed with [uv](https://docs.astral.sh/uv/).

## Setup

```bash
uv sync
```

## Common commands

```bash
uv run pytest        # run tests
uv run ruff check    # lint
uv run ty check      # type check
uv run python ...    # run scripts
```

## Dev dependencies

Includes `nicegui` and `streamlit` as dev deps for example scripts.
Includes `ty` for type checking and `ruff` for linting.

## Publishing workflow

Only wheels are built and published — no sdist.

```bash
inv check        # lint (ruff) + nbcheck examples
inv build        # clean → update README → uv build --wheel
inv publish      # twine upload dist/*.whl to PyPI
inv bump         # bump patch version in pyproject.toml
```

**Important:** `bump` runs *after* publishing, not before. The correct order is: `check` → `build` → `publish` → `bump`.
