""" tasks file (see invoke.py) """

import toml
import json
import logging

from urllib import request
from urllib.error import HTTPError

from invoke import task
from pathlib import Path

logger = logging.getLogger()

root_folder = Path(__file__).parent


def get_config(item=None, default=None):
    """ Parse pyproject.toml file """
    pyproject = root_folder.joinpath("pyproject.toml").resolve(strict=True)
    data = toml.load(pyproject)

    if item is not None:
        for i in item.split("."):
            data = data.get(i, None)
            if data is None:
                return default

    return data


@task
def clean(ctx):
    """ Clean build and dist folders """
    patterns = ['build', 'dist']
    for pattern in patterns:
        ctx.run("rm -rf {}".format(pattern))


@task
def build(ctx):
    """ Build wheel with python -mbuild """
    ctx.run("python -mbuild --wheel")


@task
def dump(ctx):
    """ Dump wheel and sdist contents """
    dist = root_folder / "dist"

    for file in dist.glob("*.whl"):
        ctx.run(f"unzip -l {file}")

    for file in dist.glob("*.tar.gz"):
        ctx.run(f"tar -ztvf {file}")


@task
def publish(ctx, test_only=False):
    """ Publish project with twine """
    if test_only:
        ctx.run("twine upload --repository testpypi dist/*")
    else:
        ctx.run("twine upload dist/*")


@task
def info(ctx):
    name = get_config("project.name")
    version = get_config("project.version")
    print("name", name)
    print("version", version)
    url = f"https://pypi.org/pypi/{name}/json"
    try:
        res = request.urlopen(url)
        data = json.load(res)
        releases = list(data["releases"])
        print("pypi.releases", releases)
    except HTTPError:
        pass
