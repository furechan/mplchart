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

Releases are built, tested, and published to PyPI when a `vX.Y.Z` tag is pushed. `.github/workflows/build.yml` is reusable and manually dispatchable; it builds only a wheel (no sdist) and tests the installed wheel on every supported Python version. `.github/workflows/release.yml` validates the tag and PyPI state, calls the build workflow, then publishes through PyPI Trusted Publishing.

```bash
inv check        # lint (ruff) + nbcheck examples
inv docs         # check + strict documentation build
inv build        # local test build only; not for publishing
inv bump         # move a plain release to the next patch .dev0 version
inv release      # test, release/tag/push, then advance to the next .dev0
```

The repository normally carries the next patch development version (`X.Y.Z.dev0`). Run `uv run inv release` from `main`: it tests, removes `.dev0`, commits and pushes the release with its tag, then commits and pushes the next patch `.dev0`. A failed release push stops before the development bump. Publish only through the tag-triggered release workflow.
