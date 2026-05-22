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
    """Lint with ruff and check example notebooks with nbcheck"""
    ctx.run("nbcheck examples")
    ctx.run("ruff check")


@task
def make(ctx):
    """Regenerate README from scripts/process-readme.py"""
    with ctx.cd("scripts"):
        ctx.run("python process-readme.py")


@task(clean, make)
def build(ctx):
    """Build project wheel (runs clean and make first)"""
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


@task
def depcheck(ctx):
    """Fetch dependabot alerts, upgrade flagged packages

    After running, review changes and commit uv.lock:
        git add uv.lock && git commit -m "Update dependencies to address security alerts"
    """
    result = ctx.run(
        "gh api repos/Furechan/mplchart/dependabot/alerts?state=open"
        " --jq '[.[].dependency.package.name] | unique[]'",
        hide=True,
    )
    packages = result.stdout.split()
    if not packages:
        print("No open Dependabot alerts.")
        return       
    print("Upgrading", *packages, "...")
    flags = " ".join(f"--upgrade-package {p}" for p in packages)
    ctx.run(f"uv sync {flags}")

