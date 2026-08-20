# mplchart

Python project managed with [uv](https://docs.astral.sh/uv/).

## Local Memory

Use local memory @.claude/memory/MEMORY.md instead of global memory.

## Architecture

See [notes/architecture.md](notes/architecture.md).

## Docs and notes

- `notes/` — internal design and engineering notes (architecture, proposals, roadmaps). Not user-facing. Put new design notes here.
- `docs/` — source of the published MkDocs documentation site (Material theme + mkdocs-jupyter, config in `mkdocs.yml`). `docs/examples` is a symlink to `examples/`; notebooks render from committed outputs (`execute: false`). Preview with `uv run mkdocs serve`, build with `uv run mkdocs build` (output in `build/site`, notebook cache in `build/cache/mkdocs-jupyter`). The site is the HTML view for humans and search engines; agents are pointed at this repo instead, where the docs are already markdown and notebooks.
- `docs/reference/*.md` — **generated** API reference; regenerate with `inv apidocs` after docstring changes, never hand-edit (exception: `reference/index.md` is hand-written). The pages are the fastest way to look up the public API. Design record: `notes/api-reference-roadmap.md`.

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
inv build        # clean → uv build --wheel
inv publish      # twine upload dist/*.whl to PyPI
inv bump         # bump patch version in pyproject.toml + uv sync
```

**Important:** `bump` runs *after* publishing, not before. The correct order is: `check` → `build` → `publish` → `bump`.
