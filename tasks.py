# noinspection PyUnresolvedReferences

import re
import json
import subprocess

from pathlib import Path
from invoke import task

PACKAGE = "mplchart"
ROOT = Path(__file__).parent


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
    flags = "--repository testpypi" if testpypi else ""
    ctx.run(f"twine upload {flags} dist/*.whl")


@task
def depcheck(ctx):
    """Fetch open Dependabot alerts, upgrade flagged packages in uv.lock, and sync

    After running, review changes and commit uv.lock:
        git add uv.lock && git commit -m "Update dependencies to address security alerts"
    """
    result = subprocess.run(
        ["gh", "api", "repos/Furechan/mplchart/dependabot/alerts",
         "--jq", "[.[] | select(.state==\"open\") | .dependency.package.name]"],
        capture_output=True, text=True, check=True
    )
    packages = list(dict.fromkeys(json.loads(result.stdout)))
    if not packages:
        print("No open Dependabot alerts.")
        return
    print(f"Upgrading: {', '.join(packages)}")
    upgrade_flags = " ".join(f"--upgrade-package {p}" for p in packages)
    ctx.run(f"uv lock {upgrade_flags}")
    ctx.run("uv sync")


@task
def bump(ctx):
    """Bump patch version in pyproject.toml"""
    pyproject = Path(__file__).joinpath("../pyproject.toml").resolve(strict=True)
    buffer = pyproject.read_text()
    pattern = r"^version \s* = \s* \"(.+)\" \s*"
    match = re.search(pattern, buffer, flags=re.VERBOSE | re.MULTILINE)
    if not match:
        raise ValueError("Could not find version setting")
    version = tuple(int(i) for i in match.group(1).split("."))
    version = version[:-1] + (version[-1] + 1,)
    version = ".".join(str(v) for v in version)
    print(f"Updating version to {version} ...")
    output = re.sub(
        pattern, f'version = "{version}"\n', buffer, flags=re.VERBOSE | re.MULTILINE
    )
    pyproject.write_text(output)
