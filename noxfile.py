# type: ignore
# pylint: disable=import-error
# pyright: reportMissingModuleSource=false

import os
import nox
import tempfile


ENVDIR = os.path.join(tempfile.gettempdir(), "envs")

nox.options.envdir = ENVDIR


@nox.session
def lint(session):
    session.install("flake8")
    session.run("flake8")


@nox.session(python=["3.8", "3.9", "3.10", "3.11"])
def tests(session: nox.Session):
    session.install(".", "pytest")
    session.run("pytest")
