# noinspection PyUnresolvedReferences

import re

from pathlib import Path
from invoke import task  # type: ignore

PACKAGE = "mplchart"
ROOT = Path(__file__).parent


@task
def info(ctx):
    """Check package versions"""
    ctx.run(f"uv pip show {PACKAGE}")


@task
def clean(ctx):
    """Cleanup and remove dist folder"""
    ctx.run("rm -rf dist")


@task
def check(ctx):
    """Check package"""
    ctx.run("nbcheck examples")
    ctx.run("ruff check")


@task
def make(ctx):
    """Update readme"""
    with ctx.cd("scripts"):
        ctx.run("python process-readme.py")


@task(clean, make)
def build(ctx):
    """Build project wheel"""
    ctx.run("uv build --wheel")


@task
def dump(ctx):
    """Dump wheel contents"""
    for file in ROOT.glob("dist/*.whl"):
        ctx.run(f"unzip -l {file}")


@task
def publish(ctx, testpypi=False):
    """Publish to PyPI with twine"""
    repoarg = "--repository testpypi" if testpypi else ""
    ctx.run(f"twine upload {repoarg} dist/*.whl")


@task
def bump(ctx):
    """Bump patch version in pyproject"""
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
