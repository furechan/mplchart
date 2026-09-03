# noinspection PyUnresolvedReferences

import re
import json
import urllib.error
import urllib.request

from pathlib import Path
from invoke.exceptions import Exit
from invoke.tasks import task

PACKAGE = "mplchart"
ROOT = Path(__file__).parent
VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:\.dev0)?$")



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
    """Move a released patch version to the next patch development version."""
    version = get_version()
    match = VERSION_PATTERN.fullmatch(version or "")
    if version is None or match is None or version.endswith(".dev0"):
        raise Exit(f"expected a plain three-part release version, found {version!r}")
    major, minor, patch = map(int, match.groups())
    next_version = f"{major}.{minor}.{patch + 1}.dev0"
    ctx.run(f"uv version --no-sync {next_version}")
    print(f"Started development of {next_version}")


@task
def release(ctx):
    """Test, commit, tag, and push the current development release."""
    branch = ctx.run("git branch --show-current", hide=True).stdout.strip()
    if branch != "main":
        print(f"Nothing to release from {branch!r}; switch to main first")
        return

    dev_version = get_version()
    match = VERSION_PATTERN.fullmatch(dev_version or "")
    if dev_version is None or match is None or not dev_version.endswith(".dev0"):
        raise Exit(f"expected a three-part .dev0 version, found {dev_version!r}")
    major, minor, patch = map(int, match.groups())
    release_version = f"{major}.{minor}.{patch}"
    next_version = f"{major}.{minor}.{patch + 1}.dev0"
    tag = f"v{release_version}"

    ctx.run("pytest")

    ctx.run(f"uv version --no-sync {release_version}")
    ctx.run("git add pyproject.toml uv.lock")
    ctx.run(f'git commit -m "Release version {release_version}"')
    ctx.run(f'git tag -a {tag} -m "Release {release_version}"')
    ctx.run(f"git push origin main {tag}")

    ctx.run(f"uv version --no-sync {next_version}")
    ctx.run("git add pyproject.toml uv.lock")
    ctx.run(f'git commit -m "Start development of {next_version}"')
    ctx.run("git push origin main")
    print(f"Pushed {tag} for release and advanced main to {next_version}")
