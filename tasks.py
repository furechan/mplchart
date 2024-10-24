# noinspection PyUnresolvedReferences

import re

from pathlib import Path
from invoke import task  # type: ignore

PACKAGE = "mplchart"
FOLDER = Path(__file__).parent


@task
def setup(ctx):
    """Install package with extras"""
    ctx.run('pip install "numpy<2.0.0"')
    ctx.run('pip install -e ".[dev]"')


@task
def info(ctx):
    """Check package versions"""
    ctx.run(f"pip index versions {PACKAGE}")


@task
def clean(ctx):
    """Clean project dist"""
    ctx.run("rm -rf dist")


@task
def check(ctx):
    """Check package"""
    ctx.run("pip install -q ruff nbcheck")
    ctx.run("nbcheck examples misc")
    ctx.run("ruff check")


@task(clean)
def build(ctx):
    """Build project wheel"""
    ctx.run("pip install -q build")
    ctx.run("python -mbuild --wheel")


@task
def dump(ctx):
    """Dump wheel contents"""
    for file in FOLDER.glob("dist/*.whl"):
        ctx.run(f"unzip -l {file}")


@task
def publish(ctx):
    """Publish to PyPI with twine"""
    ctx.run("pip install -q twine")
    ctx.run("twine upload dist/*.whl")


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
