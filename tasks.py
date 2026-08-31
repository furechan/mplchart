# noinspection PyUnresolvedReferences

import os
import re
import json
import subprocess
import urllib.error
import urllib.request

from pathlib import Path
from invoke.exceptions import Exit
from invoke.tasks import task

PACKAGE = "mplchart"
ROOT = Path(__file__).parent



def get_version() -> str | None:
    """Get version from pyproject."""
    data = ROOT.joinpath("pyproject.toml").read_text()
    pattern = r'^version \s* = \s* "(.+)" \s*'
    match = re.search(pattern, data, flags=re.VERBOSE | re.MULTILINE)
    return match.group(1) if match else None


def latest_pypi_version() -> str:
    """Get the latest published version from PyPI."""
    url = f"https://pypi.org/pypi/{PACKAGE}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.load(response)["info"]["version"]
    except urllib.error.HTTPError as error:
        raise Exit(f"could not get the latest PyPI version: HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise Exit(f"could not get the latest PyPI version: {error.reason}") from error
    except (KeyError, TypeError, ValueError) as error:
        raise Exit("could not read the latest version from PyPI's response") from error


@task
def info(ctx):
    """Show the current project version and the latest version on PyPI."""
    version = get_version()
    pypi_version = latest_pypi_version()
    print(f"Current version: {version}")
    print(f"Latest on PyPI: {pypi_version}")


@task
def clean(ctx):
    """Remove dist folder"""
    ctx.run("rm -rf dist")


@task
def apidocs(ctx):
    """Regenerate the API reference pages in docs/reference from docstrings"""
    ctx.run("uv run python scripts/make-api-docs.py")


@task
def gallery(ctx):
    """Re-execute the docs gallery notebook in place"""
    ctx.run("jupyter nbconvert --to notebook --execute --inplace docs/gallery.ipynb")


@task
def check(ctx):
    """Lint with ruff and check notebooks with nbcheck (validity + executed outputs)"""
    ctx.run("nbcheck -x examples docs docs/articles")
    ctx.run("ruff check")


@task(check, apidocs, gallery)
def docs(ctx):
    """Check the project and build the documentation."""
    ctx.run("mkdocs build --strict")



@task(clean)
def build(ctx):
    """Build a local project wheel (runs clean first)"""
    print("Warning: local builds are not for publishing; use the release workflow.")
    ctx.run("uv build --wheel")


@task
def dump(ctx):
    """List contents of the built wheel"""
    for file in ROOT.glob("dist/*.whl"):
        ctx.run(f"unzip -l {file}")


@task
def bump(ctx):
    """Bump patch version in pyproject.toml (re-locks and syncs)"""
    ctx.run("uv version --bump patch")
