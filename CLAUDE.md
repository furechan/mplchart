# mplchart

Python project managed with [uv](https://docs.astral.sh/uv/).

## Local Memory

Use local memory @.claude/memory/MEMORY.md instead of global memory.

## Architecture

See [docs/architecture.md](docs/architecture.md).

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

Includes `ty` for type checking and `ruff` for linting.

## Publishing workflow

Only wheels are built and published — no sdist.

```bash
inv check        # lint (ruff) + nbcheck examples
inv build        # clean → update README → uv build --wheel
inv publish      # twine upload dist/*.whl to PyPI
inv bump         # bump patch version in pyproject.toml + uv sync
```

**Important:** `bump` runs *after* publishing, not before. The correct order is: `check` → `build` → `publish` → `bump`.
