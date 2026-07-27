# noinspection PyUnresolvedReferences

import os
import json
import subprocess

from pathlib import Path
from invoke import task

PACKAGE = "mplchart"
ROOT = Path(__file__).parent


def load_direnv(path: str | Path = ROOT):
    """Load direnv environment for `path` in os.environ. Requires direnv installed."""
    output = subprocess.check_output(
        ["direnv", "export", "json"],
        cwd=path,
        text=True
        )
    if output:
        data = json.loads(output)
        for k, v in data.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


load_direnv()


@task
def info(ctx):
    """Show installed package version"""
    ctx.run(f"uv pip show {PACKAGE}")


@task
def clean(ctx):
    """Remove dist folder"""
    ctx.run("rm -rf dist")


@task
def check(ctx):
    """Lint with ruff and check notebooks with nbcheck (validity + executed outputs)"""
    ctx.run("nbcheck -x examples docs docs/articles")
    ctx.run("ruff check")


@task
def apidocs(ctx):
    """Regenerate the API reference pages in docs/reference from docstrings"""
    ctx.run("uv run python scripts/make-api-docs.py")


@task
def gallery(ctx):
    """Re-execute the docs gallery notebook in place"""
    ctx.run("jupyter nbconvert --to notebook --execute --inplace docs/gallery.ipynb")


@task(clean)
def build(ctx):
    """Build project wheel (runs clean first)"""
    ctx.run("uv build --wheel")


@task
def dump(ctx):
    """List contents of the built wheel"""
    for file in ROOT.glob("dist/*.whl"):
        ctx.run(f"unzip -l {file}")


@task
def publish(ctx, testpypi=False):
    """Upload dist/*.whl to PyPI via twine (use --testpypi for TestPyPI)

    Publishing order: check → build → publish → bump
    Note: bump runs *after* publishing, not before.
    """
    flags = "--skip-existing"
    if testpypi:
        flags += " --repository testpypi"
    ctx.run(f"twine upload {flags} dist/*.whl")


@task
def bump(ctx):
    """Bump patch version in pyproject.toml (re-locks and syncs)"""
    ctx.run("uv version --bump patch")
