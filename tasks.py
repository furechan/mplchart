# noinspection PyUnresolvedReferences

import re
from pathlib import Path
from invoke import task  # type: ignore

PACKAGE = "mplchart"
FOLDER = Path(__file__).parent


@task
def setup(c):
    """Check package versions"""
    c.run("pip install \"numpy<2.0.0\"")
    c.run("pip install -e \".[extras]\"")


@task
def info(c):
    """Check package versions"""
    c.run(f"pip index versions {PACKAGE}")


@task
def clean(c):
    """Clean project dist"""
    c.run("rm -rf dist")


@task
def check(c):
    """Check package"""
    c.run("pip install -q ruff nbcheck")
    c.run("nbcheck examples misc")
    c.run("ruff check")


@task(clean)
def build(c):
    """Build project wheel"""
    c.run("pip install -q build")
    c.run("python -mbuild --wheel")


@task
def dump(c):
    """Dump wheel contents"""
    for file in FOLDER.glob("dist/*.whl"):
        c.run(f"unzip -l {file}")


@task
def publish(c):
    """Publish to PyPI with twine"""
    c.run("pip install -q twine")
    c.run("twine upload dist/*.whl")

@task
def bump(c):
    """Bump patch version in pyproject"""
    pyproject = Path(__file__).joinpath("../pyproject.toml").resolve(strict=True)
    buffer = pyproject.read_text()
    pattern = r"^version \s* = \s* \"(.+)\" \s*"
    match = re.search(pattern, buffer, flags=re.VERBOSE | re.MULTILINE)
    if not match:
        raise ValueError("Could not find version setting")
    version = tuple(int(i) for i in match.group(1).split("."))
    version = version[:-1] + (version[-1]+1, )
    version = ".".join(str(v) for v in version)
    print(f"Updating version to {version} ...")
    buffer = print(re.sub(pattern, f"version = \"{version}\"\n", buffer, flags=re.VERBOSE | re.MULTILINE))
    pyproject.write_text(buffer)
