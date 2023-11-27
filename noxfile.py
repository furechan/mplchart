import os
import nox
import tempfile

ENVDIR = os.path.join(tempfile.gettempdir(), "envs")

nox.options.envdir = ENVDIR

if os.getenv("CONDA_DEFAULT_ENV"):
    nox.options.default_venv_backend = "conda"


@nox.session
def lint(session):
    session.install("flake8")
    session.run("flake8")


@nox.session(python=["3.8", "3.9", "3.10", "3.11"])
def tests(session: nox.Session):
    session.install('.', 'pytest')
    session.run('pytest')

