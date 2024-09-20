# noinspection PyUnresolvedReferences

from pathlib import Path
from invoke import task  # type: ignore

PACKAGE = "mplchart"
FOLDER = Path(__file__).parent


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
